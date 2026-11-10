import unittest

from liblathe.op.face import FaceOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.tool.tool import Tool, ToolSide


class test_FaceOP(unittest.TestCase):
    """Test for face_op.py"""

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

        partSegments.append(Segment(PartPt1, PartPt2, -0.75))
        partSegments.append(Segment(PartPt2, PartPt3))
        partSegments.append(Segment(PartPt3, PartPt4))
        partSegments.append(Segment(PartPt4, PartPt5))
        partSegments.append(Segment(PartPt5, PartPt6))
        partSegments.append(Segment(PartPt6, PartPt8))
        partSegments.append(Segment(PartPt7, PartPt8))

        # Define stock bounds
        stockPt1 = Point(0, 15)
        stockPt2 = Point(-25, -55)
        stock_boundbox = BoundBox(stockPt1, stockPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['allow_grooving'] = False
        params['pass_offset'] = 1
        params['finish_passes'] = 2
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = FaceOP()
        self.op.setParams(params)
        self.op.add_stock(stock_boundbox)
        self.op.addPartSegments(partSegments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        self.op.add_tool(tool)

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

    def test_far_side_publishes_physical_clearing_paths(self):
        operation = FaceOP()
        self.assertEqual(operation.clearing_paths, [])
        operation.setParams({'pass_offset': 1, 'stock_to_leave': 0, 'hfeed': self.hfeed, 'vfeed': 10})
        operation.add_stock(BoundBox(Point(-25, -55), Point(0, 15)))
        operation.addPartSegments([Segment(Point(-13, 10), Point(-13, -48))])
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        tool.side = ToolSide.FAR
        operation.add_tool(tool)
        stale = SegmentGroup()
        stale.addSegment(Segment(Point(99, 99), Point(98, 98)))
        operation.clearing_paths = [stale]

        commands = operation.getGCode()

        self.assertTrue(operation.clearing_paths)
        self.assertNotIn(stale, operation.clearing_paths)
        points = [(segment.start.X, segment.start.Z, segment.end.X, segment.end.Z)
                  for group in operation.clearing_paths for segment in group.getSegments()]
        self.assertTrue(all(x <= 1e-6 for point in points for x in (point[0], point[2])))
        command_x = {round(command.getParams()['X'], 6) for command in commands
                     if 'X' in command.getParams()}
        path_x = {round(x, 6) for point in points for x in (point[0], point[2])}
        self.assertTrue(path_x <= command_x, path_x - command_x)


if __name__ == '__main__':
    unittest.main()
