import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.point import Point
from liblathe.base.boundbox import BoundBox


class test_boundbox(unittest.TestCase):
    """Test for boundbox.py"""
    def setUp(self):
        self.pt1 = Point(0, 0)
        self.pt2 = Point(100, 100)
        self.boundBox1 = BoundBox(self.pt1, self.pt2)

        self.pt3 = Point(-100, -100.5)
        self.pt4 = Point(100, 100)
        self.boundBox2 = BoundBox(self.pt3, self.pt4)

    def test_XLength(self):
        xlen = self.boundBox1.XLength()
        self.assertEqual(xlen, 100)

        xlenNegative = self.boundBox2.XLength()
        self.assertEqual(xlenNegative, 200)

    def test_ZLength(self):
        zlen = self.boundBox1.ZLength()
        self.assertEqual(zlen, 100)

        zlenNegative = self.boundBox2.ZLength()
        self.assertEqual(zlenNegative, 200.5)


if __name__ == '__main__':
    unittest.main()
