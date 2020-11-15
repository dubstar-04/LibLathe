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
        length = self.tool.edge_length
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

        with self.assertRaises(Warning):
            self.tool.get_edge_length("A", "A")

        with self.assertRaises(Warning):
            self.tool.get_edge_length("D", "A")

    def test_get_nose_radius(self):
        noseRadius = self.tool.get_nose_radius("04")
        self.assertEqual(noseRadius, 0.4)

        with self.assertRaises(Warning):
            self.tool.get_nose_radius("A")

    def test_get_cutting_direction(self):
        cuttingDirection = self.tool.get_cutting_direction()
        self.assertEqual(cuttingDirection, "R")

    def test_get_rotation(self):
        rotation = self.tool.get_rotation()
        self.assertEqual(rotation, 0)

    def test_get_max_doc(self):
        max_doc = self.tool.get_max_doc()
        self.assertEqual(max_doc, 1.5875)

        with self.assertRaises(Warning):
            tool = Tool()
            max_doc = tool.get_max_doc()

    def test_set_tip_angle(self):
        self.tool.set_tip_angle(22.5)
        self.assertEqual(self.tool.tip_angle, 22.5)

        with self.assertRaises(Warning):
            self.tool.set_tip_angle("A")

        with self.assertRaises(Warning):
            self.tool.set_tip_angle(-1)

    def test_set_edge_length(self):
        self.tool.set_edge_length(5)
        self.assertEqual(self.tool.edge_length, 5)

        with self.assertRaises(Warning):
            self.tool.set_edge_length("A")

        with self.assertRaises(Warning):
            self.tool.set_edge_length(-1)

    def test_set_nose_radius(self):
        self.tool.set_nose_radius(0.5)
        self.assertEqual(self.tool.nose_radius, 0.5)

        with self.assertRaises(Warning):
            self.tool.set_nose_radius("A")

        with self.assertRaises(Warning):
            self.tool.set_nose_radius(-1)

    def test_set_direction(self):
        self.tool.set_direction("N")
        self.assertEqual(self.tool.direction, "N")

        with self.assertRaises(Warning):
            self.tool.set_direction("A")

    def test_set_rotation(self):
        self.tool.set_rotation(45)
        self.assertEqual(self.tool.rotation, 45)

        self.tool.set_rotation(22.5)
        self.assertEqual(self.tool.rotation, 22.5)

        with self.assertRaises(Warning):
            self.tool.set_rotation(361)

        with self.assertRaises(Warning):
            self.tool.set_rotation(-1)

        with self.assertRaises(Warning):
            self.tool.set_rotation("A")

    def test_set_orientation(self):
        self.tool.set_orientation(ToolOri.X)
        self.assertEqual(self.tool.orientation, ToolOri.X)

        with self.assertRaises(Warning):
            self.tool.set_orientation("X")


if __name__ == '__main__':
    unittest.main()
