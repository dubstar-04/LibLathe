import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(os.path.dirname(thisFolder))
sys.path.append(parentFolder)
from LibLathe.LLPoint import Point
from LibLathe.LLBoundBox import BoundBox


class test_boundbox(unittest.TestCase):
    """Test for LLBoundBox.py"""
    def setUp(self):
        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(100, 100, 100)
        self.boundBox1 = BoundBox(self.pt1, self.pt2)

        self.pt3 = Point(-100, -100, -100.5)
        self.pt4 = Point(100, 100, 100)
        self.boundBox2 = BoundBox(self.pt3, self.pt4)

    def test_XLength(self):
        xlen = self.boundBox1.XLength()
        self.assertEqual(xlen, 100)

        xlenNegative = self.boundBox2.XLength()
        self.assertEqual(xlenNegative, 200)

    def test_YLength(self):
        ylen = self.boundBox1.YLength()
        self.assertEqual(ylen, 100)

        ylenNegative = self.boundBox2.YLength()
        self.assertEqual(ylenNegative, 200)

    def test_ZLength(self):
        zlen = self.boundBox1.YLength()
        self.assertEqual(zlen, 100)

        zlenNegative = self.boundBox2.ZLength()
        self.assertEqual(zlenNegative, 200.5)


if __name__ == '__main__':
    unittest.main()
