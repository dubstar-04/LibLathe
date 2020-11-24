import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.point import Point
from liblathe.boundbox import BoundBox


class test_boundbox(unittest.TestCase):
    """Test for boundbox.py"""
    def setUp(self):
        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(100, 100, 100)
        self.boundBox1 = BoundBox(self.pt1, self.pt2)

        self.pt3 = Point(-100, -100, -100.5)
        self.pt4 = Point(100, 100, 100)
        self.boundBox2 = BoundBox(self.pt3, self.pt4)

    def test_x_length(self):
        xlen = self.boundBox1.x_length()
        self.assertEqual(xlen, 100)

        xlenNegative = self.boundBox2.x_length()
        self.assertEqual(xlenNegative, 200)

    def test_y_length(self):
        ylen = self.boundBox1.y_length()
        self.assertEqual(ylen, 100)

        ylenNegative = self.boundBox2.y_length()
        self.assertEqual(ylenNegative, 200)

    def test_z_length(self):
        zlen = self.boundBox1.y_length()
        self.assertEqual(zlen, 100)

        zlenNegative = self.boundBox2.z_length()
        self.assertEqual(zlenNegative, 200.5)


if __name__ == '__main__':
    unittest.main()
