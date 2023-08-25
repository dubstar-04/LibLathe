import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
opFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(opFolder)
sys.path.append(parentFolder)

from liblathe.op.rough import RoughOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.tool.tool import Tool


class test_RoughOP(unittest.TestCase):
    """Test for rough_op.py"""

    def setUp(self):

        # Define Part Geometry
        part_segments = []

        PartPt1 = Point(0, 10)
        PartPt2 = Point(5, -9)
        PartPt3 = Point(9.5, -15.85)
        PartPt4 = Point(5.4, -22)
        PartPt5 = Point(5.4, -40)
        PartPt6 = Point(13, -45)
        PartPt7 = Point(13, -48)
        PartPt8 = Point(0, -48)

        part_segments.append(Segment(PartPt1, PartPt2, 0.75))
        part_segments.append(Segment(PartPt2, PartPt3))
        part_segments.append(Segment(PartPt3, PartPt4))
        part_segments.append(Segment(PartPt4, PartPt5))
        part_segments.append(Segment(PartPt5, PartPt6))
        part_segments.append(Segment(PartPt6, PartPt7))
        part_segments.append(Segment(PartPt7, PartPt8))

        # Define stock bounds
        stockPt1 = Point(0, 15)
        stockPt2 = Point(25, -47.5)
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
        params['finish_passes'] = 2
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = RoughOP()
        self.op.set_params(params)
        self.op.add_stock(stock_boundbox)
        self.op.add_part_edges(part_segments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        # tool.set_rotation(45)
        self.op.add_tool(tool)

    def test_get_gcode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.get_gcode()

        # check there is a return list
        self.assertTrue(len(gcode))

        # get the minimum z value
        min_z = 0

        for command in gcode:

            #print(command.get_movement(), command.get_params())

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
                
                # capture the min z value
                if "Z" in command.get_params():
                    min_z = min(command.get_params()['Z'], min_z)

        # test the z value matches the stock z_min
        self.assertEqual(min_z, self.op.stock.z_min)


if __name__ == '__main__':
    unittest.main()
