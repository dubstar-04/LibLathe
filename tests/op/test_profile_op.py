import unittest

from liblathe.op.profile import ProfileOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import Path as GCodePath
from liblathe.tool.tool import Tool, ToolSide


class test_ProfileOP(unittest.TestCase):
    """Test for profile_op.py"""

    def setUp(self):

        # Define Part Geometry
        partSegments = []

        PartPt1 = Point(0, 10)
        PartPt2 = Point(5, -9)
        PartPt3 = Point(9.5, -15.85)
        PartPt4 = Point(5.4, -22)
        PartPt5 = Point(5.4, -30)
        PartPt6 = Point(5.4, -35)
        PartPt7 = Point(5.4, -40)
        PartPt8 = Point(13, -45)
        PartPt9 = Point(13, -48)
        PartPt10 = Point(0, -48)

        partSegments.append(Segment(PartPt1, PartPt2, 0.75))
        partSegments.append(Segment(PartPt2, PartPt3))
        partSegments.append(Segment(PartPt3, PartPt4))
        partSegments.append(Segment(PartPt4, PartPt5, -0.25))
        partSegments.append(Segment(PartPt5, PartPt6))
        partSegments.append(Segment(PartPt6, PartPt7))
        partSegments.append(Segment(PartPt7, PartPt8))
        partSegments.append(Segment(PartPt8, PartPt9))
        partSegments.append(Segment(PartPt9, PartPt10))

        # Define containment bounds
        containmentPt1 = Point(0, 15)
        containmentPt2 = Point(25, -55)
        containment_bounds = BoundBox(containmentPt1, containmentPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['allow_grooving'] = True
        params['pass_offset'] = 1
        params['finish_passes'] = 3
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = ProfileOP()
        self.op.setParams(params)
        self.op.add_containment(containment_bounds)
        self.op.addPartSegments(partSegments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        # tool.set_rotation(45)
        self.op.add_tool(tool)

    def stock_routing_case(self):
        tool = Tool()
        vertices = [(-0.4, -0.4), (-0.4, 2), (2, 2), (2, -0.4), (-0.4, -0.4)]
        tool.set_tool_from_segments([
            Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
        operation = ProfileOP()
        operation.add_tool(tool)
        operation.add_containment(BoundBox(Point(0, -20), Point(12, 1)))
        vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
        operation.addPartSegments([
            Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(10.5, 1), Point(10.5, -18)))
        passes.addSegment(Segment(Point(11.5, -5), Point(11.5, -18)))
        return operation, passes

    def test_rapids_keep_the_full_insert_outside_original_stock(self):
        operation, passes = self.stock_routing_case()
        operation.add_stock(operation.containment)
        operation.add_containment(BoundBox(Point(0, -20), Point(15, 3)))
        path = GCodePath()
        path.fromSegmentGroup(operation, passes, protect_part=True)
        bounds = operation.tool.get_segmentgroup().boundbox()
        position = None
        for command in path.commands:
            if command.get_movement() not in ("G0", "G1"):
                continue
            parameters = command.getParams()
            end = (parameters.get("X", position[0] if position else 0),
                   parameters.get("Z", position[1] if position else 0))
            if command.get_movement() == "G0":
                start = position or end
                outside_radius = min(start[0], end[0]) + bounds.XMin >= operation.stock.XMax - 1e-5
                above_stock = min(start[1], end[1]) + bounds.ZMin >= operation.stock.ZMax - 1e-5
                below_stock = max(start[1], end[1]) + bounds.ZMax <= operation.stock.ZMin + 1e-5
                self.assertTrue(outside_radius or above_stock or below_stock, (start, end))
            position = end

    def test_unsafe_approach_does_not_publish_partial_commands(self):
        operation, _ = self.stock_routing_case()
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(5, -10), Point(5, -12)))
        path = GCodePath()
        with self.assertRaises(ValueError):
            path.fromSegmentGroup(operation, passes, protect_part=True)
        self.assertEqual(len(path.commands), 1)
        self.assertEqual(path.commands[0].get_movement(), "G18")

    def test_invalid_stock_clearance_is_rejected(self):
        operation, passes = self.stock_routing_case()
        for clearance in (-1, float("nan"), float("inf")):
            with self.subTest(clearance=clearance):
                operation.clearance = clearance
                path = GCodePath()
                with self.assertRaises(ValueError):
                    path.fromSegmentGroup(operation, passes, protect_part=True)
                self.assertEqual(len(path.commands), 1)

    def test_bounded_leadin_follows_tool_reference_translation(self):
        lengths = []
        for radial_shift, axial_shift in ((0, 0), (0.6, 0.8)):
            operation, _ = self.stock_routing_case()
            tool = Tool()
            tool.set_tool_from_segments([
                Segment(Point(edge.start.X - radial_shift, edge.start.Z - axial_shift),
                        Point(edge.end.X - radial_shift, edge.end.Z - axial_shift), edge.bulge)
                for edge in operation.tool.get_segmentgroup().getSegments()])
            operation.add_tool(tool)
            operation.add_containment(BoundBox(Point(radial_shift, -20 + axial_shift),
                                               Point(12 + radial_shift, 1 + axial_shift)))
            group = SegmentGroup()
            operation._add_lead(group, Point(10.5 + radial_shift, -0.5 + axial_shift),
                                operation.leadin_angle, operation.containment, lead_in=True)
            lengths.append(group.getSegments()[0].getLength())
        self.assertAlmostEqual(*lengths, delta=0.02)

    def test_profile_leadins_are_axial(self):
        self.op.generatePath()
        self.assertTrue(self.op.tool_paths)
        for group in self.op.tool_paths:
            lead = group.getSegments()[0]
            self.assertAlmostEqual(lead.start.X, lead.end.X, places=5)
            self.assertGreater(lead.start.Z, lead.end.Z)

    def test_stock_allowance_preserves_front_face_and_inner_entry(self):
        operation = ProfileOP()
        tool = Tool()
        vertices = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
        tool.set_tool_from_segments([
            Segment(Point(*start), Point(*end))
            for start, end in zip(vertices, vertices[1:])])
        operation.add_tool(tool)
        operation.add_containment(BoundBox(Point(0, -19), Point(25, 5)))
        vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
        operation.addPartSegments([
            Segment(Point(*start), Point(*end))
            for start, end in zip(vertices, vertices[1:])])
        operation.stock_to_leave = 1
        operation.finish_passes = 3
        operation.pass_offset = 0.5
        operation.generatePath()
        self.assertEqual(len(operation.tool_paths), 3)
        for index, group in enumerate(operation.tool_paths):
            radius = index * operation.pass_offset
            front = [edge for edge in group.getSegments()
                     if abs(edge.start.X - edge.end.X) > 1
                     and min(edge.start.Z, edge.end.Z) > 0]
            self.assertTrue(front, "Profile must retain its front-face cutting segment")
            self.assertAlmostEqual(front[0].start.X, radius, delta=0.05)
            for edge in front:
                for point in (edge.start, edge.end):
                    self.assertAlmostEqual(point.Z, 1 + radius, delta=0.05)
            for edge in group.getSegments():
                operation.partSegmentGroup.validateToolSweep(
                    operation.tool.get_segmentgroup(), edge.start, edge.end)

    def test_fixed_offsets_meet_regularly_spaced_axial_entries(self):
        base = SegmentGroup()
        base.addSegment(Segment(Point(0, 0), Point(8, -8), 0.41421356))
        base = base.offset(0)
        self.op.add_containment(BoundBox(Point(0, -7), Point(20, 2)))
        self.op.finish_passes = 3
        for step in (0.5, 1, 2):
            with self.subTest(step=step):
                self.op.pass_offset = step
                contours = list(self.op._profile_offsets(base))
                self.assertEqual(len(contours), self.op.finish_passes)
                starts = [group.getSegments()[0].start.X for group in contours]
                for inner, outer in zip(starts, starts[1:]):
                    self.assertAlmostEqual(outer - inner, step, delta=1e-4)
                for index in range(self.op.finish_passes):
                    for segment in contours[index].getSegments():
                        for point in (segment.start, segment.end,
                                      Point((segment.start.X + segment.end.X) / 2,
                                            (segment.start.Z + segment.end.Z) / 2)):
                            self.assertAlmostEqual(base.sdv(point), step * index, delta=0.05)
                self.assertGreater(contours[1].getSegments()[0].start.Z, 0)

    def test_extended_offsets_do_not_change_default_extraction(self):
        base = SegmentGroup()
        base.addSegment(Segment(Point(0, 0), Point(8, -8), 0.41421356))
        normal = base.offset(1)
        extended = base.offset(1, extend_start=True)
        self.assertLessEqual(normal.boundbox().ZMax, 0)
        self.assertGreater(extended.boundbox().ZMax, 0.9)
        repeated = base.offset(1)
        self.assertEqual([(s.start.X, s.start.Z, s.end.X, s.end.Z)
                          for s in normal.getSegments()],
                         [(s.start.X, s.start.Z, s.end.X, s.end.Z)
                          for s in repeated.getSegments()])

    def test_straight_wall_keeps_nominal_pass_count(self):
        base = SegmentGroup()
        base.addSegment(Segment(Point(5, 0), Point(5, -8)))
        self.op.add_containment(BoundBox(Point(0, -7), Point(20, 2)))
        self.assertEqual(len(list(self.op._profile_offsets(base))), self.op.finish_passes)

    def test_leading_radial_face_does_not_force_entry_subdivision(self):
        base = SegmentGroup()
        base.addSegment(Segment(Point(0, 0), Point(5, 0)))
        base.addSegment(Segment(Point(5, 0), Point(5, -8)))
        self.op.add_containment(BoundBox(Point(0, -7), Point(20, 2)))
        contours = list(self.op._profile_offsets(base))
        self.assertEqual(len(contours), self.op.finish_passes)
        starts = [contour.getSegments()[0].start.X for contour in contours]
        for a, b in zip(starts, starts[1:]):
            self.assertLessEqual(abs(b - a), self.op.pass_offset + 1e-4)

    def test_missing_entry_intersection_fails_explicitly(self):
        contour = SegmentGroup()
        contour.addSegment(Segment(Point(5, 0), Point(5, -8)))
        with self.assertRaisesRegex(ValueError, "does not intersect"):
            self.op._trim_entry(contour, 4)

    def test_zero_and_invalid_profile_pass_parameters(self):
        base = SegmentGroup()
        base.addSegment(Segment(Point(5, 0), Point(5, -8)))
        self.op.finish_passes = 0
        self.assertEqual(list(self.op._profile_offsets(base)), [])
        for value in (-1, 1.5, True):
            with self.subTest(finish_passes=value):
                self.op.finish_passes = value
                with self.assertRaises(ValueError):
                    list(self.op._profile_offsets(base))
        self.op.finish_passes = 3
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(pass_offset=value):
                self.op.pass_offset = value
                with self.assertRaises(ValueError):
                    list(self.op._profile_offsets(base))

    def test_getGCode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.getGCode()

        # check there is a return list
        self.assertTrue(len(gcode))

        for command in gcode:

            # check the command is a liblathe.command.Command
            self.assertTrue(isinstance(command, Command))

            # check the command movement contains the a 'G'
            self.assertTrue(command.get_movement().startswith("G"))

            if command.get_movement() in ["G0", "G1", "G2", "G3"]:
                # check command has feed rate
                feed_exists = True if "F" in command.getParams() else False
                self.assertTrue(feed_exists)

                # check the feed rate
                if feed_exists:
                    self.assertEqual(command.getParams()['F'], self.hfeed)

    def test_offsets_and_leads_stay_inside_partial_containment(self):
        self.op.add_containment(BoundBox(Point(6, -30), Point(12, -10)))
        self.op.finish_passes = 16
        self.op.generatePath()
        self.assertTrue(self.op.tool_paths)
        for group in self.op.tool_paths:
            bounds = group.boundbox()
            self.assertGreaterEqual(bounds.XMin, 6 - 1e-4)
            self.assertLessEqual(bounds.XMax, 12 + 1e-4)
            self.assertGreaterEqual(bounds.ZMin, -30 - 1e-4)
            self.assertLessEqual(bounds.ZMax, -10 + 1e-4)

    def test_clipping_splits_strokes_without_bridging_excluded_region(self):
        self.op.add_containment(BoundBox(Point(0, 0), Point(10, 10)))
        group = SegmentGroup()
        vertices = [(5, 9), (12, 9), (12, 5), (5, 5), (5, -2)]
        for start, end in zip(vertices, vertices[1:]):
            group.addSegment(Segment(Point(*start), Point(*end)))
        strokes = self.op._clip_path(group)
        self.assertEqual(len(strokes), 2)
        self.assertTrue(strokes[0].getSegments()[-1].end.isSame(Point(10, 9)))
        self.assertTrue(strokes[1].getSegments()[0].start.isSame(Point(10, 5)))
        self.assertTrue(strokes[1].getSegments()[-1].end.isSame(Point(5, 0)))

    def test_clipping_keeps_boundary_lines_and_omits_outside_or_tangent_lines(self):
        bounds = (0, 10, 0, 10)
        edge = self.op._clip(Segment(Point(0, -2), Point(0, 12)), *bounds)
        self.assertTrue(edge.start.isSame(Point(0, 0)))
        self.assertTrue(edge.end.isSame(Point(0, 10)))
        self.assertIsNone(self.op._clip(Segment(Point(-1, 0), Point(-1, 10)), *bounds))
        self.assertIsNone(self.op._clip(Segment(Point(-1, 1), Point(1, -1)), *bounds))
        with self.assertRaisesRegex(ValueError, "line segments"):
            self.op._clip(Segment(Point(0, 0), Point(10, 10), 0.5), *bounds)

    def test_wholly_excluded_offsets_produce_no_cutting_strokes(self):
        self.op.add_containment(BoundBox(Point(20, -30), Point(25, -10)))
        self.op.generatePath()
        self.assertEqual(self.op.tool_paths, [])

    def test_partial_profile_feeds_and_rapids_with_front_and_rear_tools(self):
        for sign in (1, -1):
            for origin in (0, -1):
                with self.subTest(sign=sign, origin=origin):
                    operation = ProfileOP()
                    operation.finish_passes = 3
                    operation.pass_offset = 0.5
                    operation.add_containment(BoundBox(Point(0, -15), Point(sign * 14, -5)))
                    operation.add_stock(BoundBox(Point(0, -20), Point(sign * 12, 0)))
                    vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
                    operation.addPartSegments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                        for a, b in zip(vertices, vertices[1:])])
                    tool = Tool()
                    vertices = [(0, origin), (0, origin + 2), (2, origin + 2),
                                (2, origin), (0, origin)]
                    tool.set_tool_from_segments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                        for a, b in zip(vertices, vertices[1:])])
                    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
                    operation.add_tool(tool)
                    moves = [c for c in operation.getGCode() if 'X' in c.getParams()]
                    self.assertTrue(operation.tool_paths)
                    for group in operation.tool_paths:
                        for segment in group.getSegments():
                            for point in (segment.start, segment.end):
                                self.assertTrue(-1e-4 <= sign * point.X <= 14 + 1e-4)
                                self.assertTrue(-15 - 1e-4 <= point.Z <= -5 + 1e-4)
                    for previous, current in zip(moves, moves[1:]):
                        a, b = previous.getParams(), current.getParams()
                        if current.get_movement() == 'G0':
                            self.assertTrue(abs(a['X'] - b['X']) < 1e-4
                                            or abs(a['Z'] - b['Z']) < 1e-4)
                            self.assertTrue(
                                min(sign * a['X'], sign * b['X']) >= 14 - 1e-4
                                or min(a['Z'], b['Z']) >= -5 - 1e-4
                                or max(a['Z'], b['Z']) <= -15 + 1e-4)
                        elif current.get_movement() == 'G1':
                            if sign * b['X'] > 14 + 1e-4:
                                self.assertGreater(sign * b['X'], sign * a['X'])
                                self.assertAlmostEqual(a['Z'], b['Z'], places=4)
                            else:
                                for point in (a, b):
                                    self.assertTrue(-1e-4 <= sign * point['X'] <= 14 + 1e-4)
                                    self.assertTrue(-15 - 1e-4 <= point['Z'] <= -5 + 1e-4)


if __name__ == '__main__':
    unittest.main()
