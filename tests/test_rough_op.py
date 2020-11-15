import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.rough_op import RoughOP
from liblathe.command import Command
from liblathe.boundbox import BoundBox
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.tool import Tool


class test_RoughOP(unittest.TestCase):
    """Test for rough_op.py"""

    def setUp(self):

        # Define Part Geometry
        part_segments = []

        PartPt1 = Point(0, 0, 10)
        PartPt2 = Point(-5, 0, -9)
        PartPt3 = Point(-9.5, 0, -15.85)
        PartPt4 = Point(-5.4, 0, -22)
        PartPt5 = Point(-5.4, 0, -40)
        PartPt6 = Point(-13, 0, -45)
        PartPt7 = Point(-13, 0, -48)
        PartPt8 = Point(0, 0, -48)

        part_segments.append(Segment(PartPt1, PartPt2, -0.75))
        part_segments.append(Segment(PartPt2, PartPt3))
        part_segments.append(Segment(PartPt3, PartPt4))
        part_segments.append(Segment(PartPt4, PartPt5))
        part_segments.append(Segment(PartPt5, PartPt6))
        part_segments.append(Segment(PartPt6, PartPt8))
        part_segments.append(Segment(PartPt7, PartPt8))

        # Define stock bounds
        stockPt1 = Point(0, 0, 15)
        stockPt2 = Point(-25, 0, -55)
        stock_boundbox = BoundBox(stockPt1, stockPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        props = {}
        props['min_dia'] = 0
        props['extra_dia'] = 0
        props['start_offset'] = 0
        props['end_offset'] = 0
        props['allow_grooving'] = False
        props['allow_facing'] = False
        props['allow_roughing'] = True
        props['allow_finishing'] = True
        props['step_over'] = 1
        props['finish_passes'] = 2
        props['hfeed'] = self.hfeed
        props['vfeed'] = 10

        self.op = RoughOP()
        self.op.set_params(props)
        self.op.add_stock(stock_boundbox)
        self.op.add_part_edges(part_segments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        self.op.add_tool(tool)

    def test_get_gcode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.get_gcode()

        # check there is a return list
        self.assertTrue(len(gcode))

        for line in gcode:
            # check the line has commands
            self.assertTrue(len(line))

            for command in line:
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
