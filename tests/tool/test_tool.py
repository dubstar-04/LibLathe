import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
toolFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(toolFolder)
sys.path.append(parentFolder)

from liblathe.tool.tool import Tool
from liblathe.tool.tool import ToolOri

from liblathe.base.segmentgroup import SegmentGroup


class test_tool(unittest.TestCase):
    """Test for tool.py"""
    def setUp(self):
        self.tool = Tool()
        self.tool.set_tool_from_string('DCMT070204R')

        self.TShapeTool = Tool()
        self.TShapeTool.set_tool_from_string('TCMT160404N')

    def test_create_tool(self):
        shape = self.tool.shape
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

    def test_getToolShape(self):
        shape = self.tool.getToolShape()
        self.assertEqual(shape, "D")

        TriangleShape = self.TShapeTool.getToolShape()
        self.assertEqual(TriangleShape, "T")

    def test_getShapeAngle(self):
        shapeAngle = self.tool.get_tip_angle_from_shape("D")
        self.assertEqual(shapeAngle, 55)

        TShapeAngle = self.TShapeTool.get_tip_angle_from_shape("T")
        self.assertEqual(TShapeAngle, 60)

    def test_get_edge_length(self):
        edgeLength = self.tool.get_edge_length("D", "07")
        self.assertEqual(edgeLength, 6.35)

        TriangleEdgeLength = self.TShapeTool.get_edge_length("T", "16")
        self.assertEqual(TriangleEdgeLength, 9.525)

        with self.assertRaises(Warning):
            self.tool.get_edge_length("A", "A")

        with self.assertRaises(Warning):
            self.tool.get_edge_length("D", "A")

    def test_get_nose_radius(self):
        noseRadius = self.tool.get_nose_radius("04")
        self.assertEqual(noseRadius, 0.4)

        TriangleNoseRadius = self.TShapeTool.get_nose_radius("04")
        self.assertEqual(TriangleNoseRadius, 0.4)

        with self.assertRaises(Warning):
            self.tool.get_nose_radius("A")

    def test_get_cutting_direction(self):
        cuttingDirection = self.tool.get_cutting_direction()
        self.assertEqual(cuttingDirection, "R")

        TriangleToolCuttingDirection = self.TShapeTool.get_cutting_direction()
        self.assertEqual(TriangleToolCuttingDirection, "N")

    def test_getRotation(self):
        rotation = self.tool.getRotation()
        self.assertEqual(rotation, 0)

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
        self.assertEqual(self.tool.tool_rotation, 45)

        self.tool.set_rotation(22.5)
        self.assertEqual(self.tool.tool_rotation, 22.5)

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

    def test_get_segmentgroup(self):
        shape = self.tool.get_segmentgroup()
        self.assertTrue(isinstance(shape, SegmentGroup))
        self.assertEqual(4, shape.count())

        triangleShape = self.TShapeTool.get_segmentgroup()
        self.assertTrue(isinstance(triangleShape, SegmentGroup))
        self.assertEqual(3, triangleShape.count())


if __name__ == '__main__':
    unittest.main()
