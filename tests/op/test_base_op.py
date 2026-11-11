import unittest

from liblathe.op.base import BaseOP, CutDirection
from liblathe.base.point import Point
from liblathe.base.boundbox import BoundBox
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.tool.tool import Tool, ToolSide


class test_BaseOP(unittest.TestCase):
    """Test for op.py"""

    def setUp(self):
        self.baseop = BaseOP()
        self.setProps = {'allow_grooving': False, 'pass_offset': 1, 'finish_passes': 1,
                         'stock_to_leave': 0.25, 'hfeed': 10, 'vfeed': 10, 'clearance': 4}
        self.getProps = {'allow_grooving': False, 'pass_offset': 1.5, 'finish_passes': 1,
                         'stock_to_leave': 0, 'hfeed': 100, 'vfeed': 50, 'clearance': 3,
                         'cut_direction': CutDirection.RADIAL}

    def test_setParams(self):
        self.baseop.setParams(self.setProps)
        self.assertEqual(self.baseop.pass_offset, 1)
        self.assertEqual(self.baseop.hfeed, 10)
        self.assertEqual(self.baseop.vfeed, 10)
        self.assertFalse(self.baseop.allow_grooving)

    def test_containment_and_stock_are_independent(self):
        self.assertIsNone(self.baseop.containment)
        self.assertIsNone(self.baseop.stock)
        self.baseop.add_containment_from_limits(0, 12, -20, -5)
        stock = BoundBox(Point(0, -30), Point(20, 5))
        self.baseop.add_stock(stock)
        self.assertIs(self.baseop.stock, stock)
        self.assertEqual(self.baseop.containment.XMax, 12)
        self.assertEqual(self.baseop.containment.ZMin, -20)
        self.assertEqual(self.baseop.containment.ZMax, -5)
        containment = BoundBox(Point(2, -15), Point(10, -8))
        self.baseop.add_containment(containment)
        self.assertIs(self.baseop.containment, containment)
        self.assertIs(self.baseop.stock, stock)

    @unittest.expectedFailure
    def test_setParams_error(self):
        # Test getGCode() with no tool set

        params = {}
        params['wrong_para'] = "error"

        self.test_op = BaseOP()

        with self.assertWarns(Warning):
            self.test_op.setParams(params)

    @unittest.expectedFailure
    def test_getGCode(self):
        # Test getGCode() with no tool set
        with self.assertWarns(Warning):
            self.baseop.getGCode()

    def test_generate_gcode(self):
        gcode = self.baseop.generateGCode()
        self.assertEqual([command.get_movement() for command in gcode], ["G18"])

    def test_far_side_reflects_copies_and_signed_output(self):
        class ReflectionProbe(BaseOP):
            def generatePath(self):
                self.planned_side = self.tool.side
                self.tool_paths = [self.partSegmentGroup]

            def generateGCode(self):
                self.assert_planning()
                return [Command("G0", {"X": 12, "Z": 3}),
                        Command("G2", {"X": 10, "Z": -5, "I": 2, "K": 1, "F": 80})]

            def assert_planning(self):
                assert self.planned_side is ToolSide.NEAR
                assert self.containment.XMin == 0 and self.containment.XMax == 15
                assert self.stock.XMin == 0 and self.stock.XMax == 20
                assert self.stock.ZMin == -25 and self.stock.ZMax == 8
                assert self.tool.segmentGroup.getSegments()[0].start.X == 10
                assert self.partSegmentGroup.getSegments()[0].start.X == 12

        operation = ReflectionProbe()
        operation.tool = Tool()
        operation.tool.side = ToolSide.FAR
        operation.tool.set_tool_from_segments([Segment(Point(-10, 0), Point(-11, 1))])
        operation.containment = BoundBox(Point(-15, -20), Point(0, 5))
        operation.add_stock(BoundBox(Point(-20, -25), Point(0, 8)))
        operation.partSegmentGroup = SegmentGroup()
        operation.partSegmentGroup.addSegment(Segment(Point(-12, 0), Point(-10, -5), 0.2))
        commands = operation.getGCode()
        self.assertEqual(commands[0].get_movement(), "G0")
        self.assertEqual(commands[0].getParams(), {"X": -12, "Z": 3})
        self.assertEqual(commands[1].get_movement(), "G3")
        self.assertEqual(commands[1].getParams(), {"X": -10, "Z": -5, "I": -2, "K": 1, "F": 80})
        self.assertIs(operation.tool.side, ToolSide.FAR)
        self.assertEqual(operation.stock.XMin, -20)
        self.assertEqual(operation.stock.XMax, 0)
        self.assertEqual(operation.tool.segmentGroup.getSegments()[0].start.X, -10)
        self.assertAlmostEqual(operation.partSegmentGroup.getSegments()[0].bulge, 0.2)
        self.assertEqual(operation.tool_paths[0].getSegments()[0].start.X, -12)
        self.assertAlmostEqual(operation.tool_paths[0].getSegments()[0].bulge, 0.2)
        self.assertEqual([command.getParams() for command in operation.getGCode()],
                         [command.getParams() for command in commands])
        operation.containment = BoundBox(Point(0, -20), Point(15, 5))
        with self.assertRaisesRegex(ValueError, "negative X"):
            operation.getGCode()

    def test_getParams(self):
        params = self.baseop.getParams()
        for i in params:
            self.assertEqual(params[i], self.getProps[i])


if __name__ == '__main__':
    unittest.main()
