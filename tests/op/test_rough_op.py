import unittest
import math
from unittest.mock import Mock

from liblathe.op.rough import RoughOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.tool.tool import Tool, ToolSide


class test_RoughOP(unittest.TestCase):
    """Test for rough_op.py"""

    def setUp(self):

        # Define Part Geometry
        partSegments = []

        PartPt1 = Point(0, 10)
        PartPt2 = Point(5, -9)
        PartPt3 = Point(9.5, -15.85)
        PartPt4 = Point(5.4, -22)
        PartPt5 = Point(5.4, -40)
        PartPt6 = Point(13, -45)
        PartPt7 = Point(13, -48)
        PartPt8 = Point(0, -48)

        partSegments.append(Segment(PartPt1, PartPt2, 0.75))
        partSegments.append(Segment(PartPt2, PartPt3))
        partSegments.append(Segment(PartPt3, PartPt4))
        partSegments.append(Segment(PartPt4, PartPt5))
        partSegments.append(Segment(PartPt5, PartPt6))
        partSegments.append(Segment(PartPt6, PartPt7))
        partSegments.append(Segment(PartPt7, PartPt8))

        # Define containment bounds
        containmentPt1 = Point(0, 15)
        containmentPt2 = Point(25, -47.5)
        containment_bounds = BoundBox(containmentPt1, containmentPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['allow_grooving'] = True
        params['pass_offset'] = 1
        params['finish_passes'] = 2
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = RoughOP()
        self.op.setParams(params)
        self.op.add_containment(containment_bounds)
        self.op.addPartSegments(partSegments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        # tool.set_rotation(45)
        self.op.add_tool(tool)

    def test_shifted_tool_reference_uses_programmed_containment(self):
        for radial_shift, axial_shift in ((0, 0), (0.6, 0.8)):
            operation = RoughOP()
            operation.stock_to_leave = 0.5
            operation.add_containment(BoundBox(Point(radial_shift, -20 + axial_shift),
                                               Point(14 + radial_shift, 1 + axial_shift)))
            vertices = ((0, 0), (10, 0), (10, -20), (0, -20))
            operation.addPartSegments([
                Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
            vertices = ((0, -1), (0, 1), (2, 1), (2, -1), (0, -1))
            tool = Tool()
            tool.set_tool_from_segments([
                Segment(Point(start[0] - radial_shift, start[1] - axial_shift),
                        Point(end[0] - radial_shift, end[1] - axial_shift))
                for start, end in zip(vertices, vertices[1:])])
            operation.add_tool(tool)
            operation.generatePath()
            bounds = [group.boundbox() for group in operation.tool_paths]
            self.assertTrue(bounds)
            for bound in bounds:
                self.assertGreaterEqual(bound.XMin, radial_shift - 1e-4)
                self.assertLessEqual(bound.XMax, 14 + radial_shift + 1e-4)
                self.assertGreaterEqual(bound.ZMin, -20 + axial_shift - 1e-4)
                self.assertLessEqual(bound.ZMax, 1 + axial_shift + 1e-4)

    def test_getGCode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.getGCode()

        # check there is a return list
        self.assertTrue(len(gcode))

        # get the minimum z value
        min_z = 0

        for command in gcode:

            # print(command.get_movement(), command.getParams())

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

                # capture the min z value
                if "Z" in command.getParams():
                    min_z = min(command.getParams()['Z'], min_z)

        self.assertAlmostEqual(min_z, self.op.containment.ZMin, places=4)

    def test_roughing_reaches_inner_containment_radius(self):
        for radius in (0, 0.001, 0.5):
            with self.subTest(radius=radius):
                self.op.add_containment(BoundBox(Point(radius, -47.5), Point(25, 15)))
                self.op.generatePath()
                self.assertTrue(self.op.tool_paths)
                inner = self.op.tool_paths[0].getSegments()[0]
                self.assertAlmostEqual(inner.start.X, radius, places=6)
                self.assertAlmostEqual(inner.end.X, radius, places=6)
                self.assertGreater(inner.start.Z, inner.end.Z)
                self.op.partSegmentGroup.validateToolSweep(
                    self.op.tool.get_segmentgroup(), inner.start, inner.end)

    def test_stock_allowance_is_preserved_at_front_of_inner_passes(self):
        reference = self.op.partSegmentGroup.defeature(
            self.op.containment, self.op.tool.get_segmentgroup(), self.op.allow_grooving)
        ends = []
        for allowance in (0, 1):
            self.op.stock_to_leave = allowance
            self.op.generatePath()
            ends.append([group.getSegments()[0].end.Z for group in self.op.tool_paths[:2]])
            if allowance:
                for group in self.op.tool_paths:
                    end = group.getSegments()[0].end
                    if end.Z > self.op.containment.ZMin + 1e-4:
                        self.assertAlmostEqual(reference.sdv(end), allowance + 0.01, delta=0.05)
        for bare, remaining in zip(*ends):
            self.assertGreater(remaining - bare, 0.9)

    def test_leads_shorten_without_changing_direction(self):
        self.op.pass_offset = 2
        self.op.partSegmentGroup = Mock()
        limits = BoundBox(Point(0, 0), Point(10, 10))
        cases = (
            (Point(9.5, 5), math.pi * 1.5, False, 0.5),
            (Point(9.5, 5), math.pi * 1.5, True, 0.5),
            (Point(0.5, 5), math.pi * 0.5, False, 0.5),
            (Point(5, 9.5), 0, False, 0.5),
            (Point(5, 0.5), math.pi, False, 0.5),
            (Point(5, 9.5), math.pi * 1.75, False, math.sqrt(0.5)),
            (Point(10, 5), math.pi * 1.5, False, 0),
            (Point(5, 5), math.pi * 1.75, False, 2),
        )
        for anchor, angle, lead_in, length in cases:
            with self.subTest(anchor=anchor, angle=angle, lead_in=lead_in):
                group = SegmentGroup()
                self.op.partSegmentGroup.reset_mock()
                self.op._add_lead(group, anchor, angle, limits, lead_in=lead_in)
                if length == 0:
                    self.assertEqual(group.count(), 0)
                    self.op.partSegmentGroup.validateToolSweep.assert_not_called()
                    continue
                segment = group.getSegments()[0]
                self.assertAlmostEqual(segment.getLength(), length, places=4)
                fixed = segment.end if lead_in else segment.start
                free = segment.start if lead_in else segment.end
                self.assertTrue(fixed.isSame(anchor))
                original = anchor.project(angle, 2)
                cross = ((free.X - anchor.X) * (original.Z - anchor.Z)
                         - (free.Z - anchor.Z) * (original.X - anchor.X))
                self.assertAlmostEqual(cross, 0, places=4)
                self.op.partSegmentGroup.validateToolSweep.assert_called_once()

    def test_colliding_lead_is_rejected(self):
        self.op.partSegmentGroup = Mock()
        self.op.partSegmentGroup.validateToolSweep.side_effect = RuntimeError("collision")
        group = SegmentGroup()
        with self.assertRaisesRegex(RuntimeError, "collision"):
            self.op._add_lead(group, Point(5, 5), math.pi * 1.5,
                              BoundBox(Point(0, 0), Point(10, 10)))
        self.assertEqual(group.count(), 0)

    def test_generated_leads_fit_cutting_limits(self):
        self.op.generatePath()
        tool = self.op.tool.get_segmentgroup()
        leads = 0
        for group in self.op.tool_paths:
            for segment in group.getSegments():
                if abs(segment.start.X - segment.end.X) > 1e-5:
                    leads += 1
                    self.op.partSegmentGroup.validateToolSweep(tool, segment.start, segment.end)
                for point in (segment.start, segment.end):
                    self.assertGreaterEqual(point.X, self.op.containment.XMin - 1e-4)
                    self.assertLessEqual(point.X, self.op.containment.XMax + 1e-4)
                    self.assertGreaterEqual(point.Z, self.op.containment.ZMin - 1e-4)
                    self.assertLessEqual(point.Z, self.op.containment.ZMax + 1e-4)
        self.assertGreater(leads, 0)

    def test_tool_reference_stays_inside_containment(self):
        for sign in (1, -1):
            for origin in (0, -1, -2):
                with self.subTest(sign=sign, origin=origin):
                    operation = RoughOP()
                    operation.pass_offset = 1
                    operation.add_containment(BoundBox(Point(sign * 0.5, -20),
                                                       Point(sign * 14.2, 1)))
                    vertices = ((0, 0), (10, 0), (10, -20), (0, -20))
                    operation.addPartSegments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                        for a, b in zip(vertices, vertices[1:])])
                    vertices = ((0, origin), (0, origin + 2), (12, origin + 2),
                                (12, origin), (0, origin))
                    tool = Tool()
                    tool.set_tool_from_segments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                        for a, b in zip(vertices, vertices[1:])])
                    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
                    operation.add_tool(tool)
                    commands = operation.getGCode()
                    self.assertTrue(commands)
                    self.assertTrue(operation.tool_paths)
                    for group in operation.tool_paths:
                        for segment in group.getSegments():
                            for point in (segment.start, segment.end):
                                self.assertGreaterEqual(sign * point.X, 0.5 - 1e-4)
                                self.assertLessEqual(sign * point.X, 14.2 + 1e-4)
                                self.assertGreaterEqual(point.Z, -20 - 1e-4)
                                self.assertLessEqual(point.Z, 1 + 1e-4)
                    moves = [c for c in commands if 'X' in c.getParams()]
                    for previous, current in zip(moves, moves[1:]):
                        if current.get_movement() == 'G1':
                            if sign * current.getParams()['X'] > 14.2 + 1e-4:
                                self.assertAlmostEqual(current.getParams()['Z'],
                                                       previous.getParams()['Z'])
                                continue
                            for command in (previous, current):
                                position = command.getParams()
                                self.assertGreaterEqual(sign * position['X'], 0.5 - 1e-4)
                                self.assertLessEqual(sign * position['X'], 14.2 + 1e-4)
                                self.assertGreaterEqual(position['Z'], -20 - 1e-4)
                                self.assertLessEqual(position['Z'], 1 + 1e-4)

    def test_containment_can_be_bigger_than_stock(self):
        self.op.add_stock(BoundBox(Point(0, -48), Point(20, 10)))
        self.op.add_containment(BoundBox(Point(0, -47.5), Point(25, 15)))
        commands = self.op.getGCode()
        moves = [c for c in commands if 'X' in c.getParams() and 'Z' in c.getParams()]
        feeds = 0
        for previous, current in zip(moves, moves[1:]):
            if current.get_movement() != 'G1':
                continue
            if current.getParams()['X'] > 25 + 1e-4:
                self.assertAlmostEqual(current.getParams()['Z'], previous.getParams()['Z'])
                continue
            feeds += 1
            for command in (previous, current):
                position = command.getParams()
                self.assertGreaterEqual(position['X'], -1e-4)
                self.assertLessEqual(position['X'], 25 + 1e-4)
                self.assertGreaterEqual(position['Z'], -47.5 - 1e-4)
                self.assertLessEqual(position['Z'], 15 + 1e-4)
        self.assertGreater(feeds, 0)
        self.assertTrue(any(c.get_movement() == 'G0' and c.getParams()['Z'] > 15
                            for c in moves))


if __name__ == '__main__':
    unittest.main()
