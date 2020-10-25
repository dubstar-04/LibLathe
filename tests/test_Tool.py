import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.tool import Tool
from liblathe.tool import ToolOri


class test_tool(unittest.TestCase):
    """Test for tool.py"""
    def setUp(self):
        self.tool = Tool('DCMT070204R')

    def test_create_tool(self):
        shape = self.tool.shape
        length = self.tool.length
        nose_radius = self.tool.nose_radius
        direction = self.tool.direction
        orientation = self.tool.orientation

        self.assertEqual(shape, "D")
        self.assertEqual(length, "07")
        self.assertEqual(nose_radius, "04")
        self.assertEqual(direction, "R")
        self.assertEqual(orientation, ToolOri.X)

        with self.assertRaises(ValueError):
            Tool('xyz')

    def test_get_tool_cutting_angle(self):
        cuttingAngle = self.tool.get_tool_cutting_angle()
        self.assertEqual(cuttingAngle, 275)

    def test_getShapeAngle(self):
        shapeAngle = self.tool.getShapeAngle()
        self.assertEqual(shapeAngle, 55)

    def test_getEdgeLength(self):
        edgeLength = self.tool.getEdgeLength()
        self.assertEqual(edgeLength, 6.35)

    def test_getCuttingDirection(self):
        cuttingDirection = self.tool.getCuttingDirection()
        self.assertEqual(cuttingDirection, "R")


if __name__ == '__main__':
    unittest.main()
