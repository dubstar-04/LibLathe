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

        # Define stock bounds
        stockPt1 = Point(0, 15)
        stockPt2 = Point(25, -47.5)
        stock_boundbox = BoundBox(stockPt1, stockPt2)

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['allow_grooving'] = True
        params['step_over'] = 1
        params['finish_passes'] = 2
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = RoughOP()
        self.op.setParams(params)
        self.op.add_stock(stock_boundbox)
        self.op.addPartSegments(partSegments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        # tool.set_rotation(45)
        self.op.add_tool(tool)

    def test_cutting_limits_follow_tool_reference_translation(self):
        limits = []
        radial_passes = []
        for radial_shift, axial_shift in ((0, 0), (0.6, 0.8)):
            operation = RoughOP()
            operation.stock_to_leave = 0.5
            operation.add_stock(BoundBox(Point(0, -20), Point(14, 1)))
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
            radial_passes.append(sorted({round(edge.start.X - radial_shift, 4)
                                         for group in operation.tool_paths for edge in group.getSegments()
                                         if abs(edge.start.X - edge.end.X) < 1e-5}))
            limits.append((min(bound.ZMin for bound in bounds) - axial_shift,
                           max(bound.ZMax for bound in bounds) - axial_shift))
        self.assertEqual(*radial_passes)
        for original, shifted in zip(*limits):
            self.assertAlmostEqual(original, shifted, delta=0.02)

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

        # test the z value matches the stock ZMin
        self.assertEqual(min_z, self.op.stock.ZMin)


if __name__ == '__main__':
    unittest.main()
