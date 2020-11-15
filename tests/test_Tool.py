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
        self.tool = Tool()
        self.tool.set_tool_from_string('DCMT070204R')

    def test_create_tool(self):
        shape = "D"
        length = self.tool.length
        nose_radius = self.tool.nose_radius
        direction = self.tool.direction
        orientation = self.tool.orientation

        self.assertEqual(shape, "D")
        self.assertEqual(length, 6.35)
        self.assertEqual(nose_radius, 0.4)
        self.assertEqual(direction, "R")
        self.assertEqual(orientation, ToolOri.X)

        with self.assertRaises(ValueError):
            Tool('xyz')

    def test_get_tool_cutting_angle(self):
        cuttingAngle = self.tool.get_tool_cutting_angle()
        self.assertEqual(cuttingAngle, 303)

    def test_getShapeAngle(self):
        shapeAngle = self.tool.get_tip_angle_from_shape("D")
        self.assertEqual(shapeAngle, 55)

    def test_get_edge_length(self):
        edgeLength = self.tool.get_edge_length("D", "07")
        self.assertEqual(edgeLength, 6.35)

    def test_get_nose_radius(self):
        noseRadius = self.tool.get_nose_radius("04")
        self.assertEqual(noseRadius, 0.4)

    def test_get_cutting_direction(self):
        cuttingDirection = self.tool.get_cutting_direction()
        self.assertEqual(cuttingDirection, "R")

    def test_get_rotation(self):
        rotation = self.tool.get_rotation()
        self.assertEqual(rotation, 0)


if __name__ == '__main__':
    unittest.main()
