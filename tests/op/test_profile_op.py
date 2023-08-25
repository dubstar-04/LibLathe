import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
opFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(opFolder)
sys.path.append(parentFolder)

from liblathe.op.profile import ProfileOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.tool.tool import Tool


class test_ProfileOP(unittest.TestCase):
    """Test for profile_op.py"""

    def setUp(self):

        # Define Part Geometry
        part_segments = []

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

        part_segments.append(Segment(PartPt1, PartPt2, 0.75))
        part_segments.append(Segment(PartPt2, PartPt3))
        part_segments.append(Segment(PartPt3, PartPt4))
        part_segments.append(Segment(PartPt4, PartPt5, -0.25))
        part_segments.append(Segment(PartPt5, PartPt6))
        part_segments.append(Segment(PartPt6, PartPt7))
        part_segments.append(Segment(PartPt7, PartPt8))
        part_segments.append(Segment(PartPt8, PartPt9))
        part_segments.append(Segment(PartPt9, PartPt10))

        # Define stock bounds
        stockPt1 = Point(0, 15)
        stockPt2 = Point(25, -55)
        stock_boundbox = BoundBox(stockPt1, stockPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['min_dia'] = 0
        params['extra_dia'] = 0
        params['start_offset'] = 0
        params['end_offset'] = 0
        params['allow_grooving'] = True
        params['step_over'] = 1
        params['finish_passes'] = 3
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = ProfileOP()
        self.op.set_params(params)
        self.op.add_stock(stock_boundbox)
        self.op.add_part_edges(part_segments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        #tool.set_rotation(45)
        self.op.add_tool(tool)

    def test_get_gcode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.get_gcode()

        # check there is a return list
        self.assertTrue(len(gcode))

        for command in gcode:

            # check the command is a liblathe.command.Command
            self.assertTrue(isinstance(command, Command))

            # check the command movement contains the a 'G'
            self.assertTrue(command.get_movement().startswith("G"))

            if command.get_movement() in ["G0", "G1", "G2", "G3"]:
                # check command has feed rate
                feed_exists = True if "F" in command.get_params() else False
                self.assertTrue(feed_exists)

                # check the feed rate
                if feed_exists:
                    self.assertEqual(command.get_params()['F'], self.hfeed)


if __name__ == '__main__':
    unittest.main()
