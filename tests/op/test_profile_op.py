import unittest

from liblathe.op.profile import ProfileOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import Path as GCodePath
from liblathe.tool.tool import Tool


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
                outside_radius = min(start[0], end[0]) + bounds.XMin > operation.containment.XMax
                above_stock = min(start[1], end[1]) + bounds.ZMin > operation.containment.ZMax
                below_stock = max(start[1], end[1]) + bounds.ZMax < operation.containment.ZMin
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

    def test_leadin_follows_tool_reference_translation(self):
        starts = []
        for radial_shift, axial_shift in ((0, 0), (0.6, 0.8)):
            operation, _ = self.stock_routing_case()
            tool = Tool()
            tool.set_tool_from_segments([
                Segment(Point(edge.start.X - radial_shift, edge.start.Z - axial_shift),
                        Point(edge.end.X - radial_shift, edge.end.Z - axial_shift), edge.bulge)
                for edge in operation.tool.get_segmentgroup().getSegments()])
            operation.add_tool(tool)
            group = SegmentGroup()
            group.addSegment(Segment(Point(10.5 + radial_shift, -0.5 + axial_shift),
                                     Point(10.5 + radial_shift, -18 + axial_shift)))
            operation.add_leadin(group)
            starts.append(group.getSegments()[0].start.Z - axial_shift)
        self.assertAlmostEqual(*starts, delta=0.02)

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


if __name__ == '__main__':
    unittest.main()
