import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(os.path.dirname(thisFolder))
sys.path.append(parentFolder)
from LibLathe.LLPoint import Point


class test_point(unittest.TestCase):
    """Test for LLPoint.py"""

    pt1 = Point(0, 0, 0)
    pt2 = Point(100, 100, 100)
    pt3 = Point(150, 130, 200)
    pt4 = Point(200, 200, 200)

    def test_distance_to(self):
        distance = Point.distance_to(self.pt1, self.pt2)
        self.assertEqual(distance, 173.20508075688772)

    def test_angle_to(self):
        angle = Point.angle_to(self.pt1, self.pt2)
        self.assertEqual(angle, 45)

    def test_nearest(self):
        pts = [self.pt2, self.pt3]
        nearest = Point.nearest(self.pt1, pts)
        self.assertEqual(nearest, self.pt2)

    def test_is_same_return_false(self):
        same = Point.is_same(self.pt1, self.pt2)
        self.assertEqual(same, False)

    def test_is_same_return_true(self):
        same = Point.is_same(self.pt1, self.pt1)
        self.assertEqual(same, True)

    def test_sub(self):
        sub = Point.sub(self.pt4, self.pt2)
        self.assertEqual(sub.X, self.pt2.X)
        self.assertEqual(sub.Y, self.pt2.Y)
        self.assertEqual(sub.Z, self.pt2.Z)

    def test_add(self):
        add = Point.add(self.pt2, self.pt2)
        self.assertEqual(add.X, self.pt4.X)
        self.assertEqual(add.Y, self.pt4.Y)
        self.assertEqual(add.Z, self.pt4.Z)

    def test_multiply(self):
        multiply = Point.multiply(self.pt2, 0)
        self.assertEqual(multiply.X, self.pt1.X)
        self.assertEqual(multiply.Y, self.pt1.Y)
        self.assertEqual(multiply.Z, self.pt1.Z)

    def test_rotate(self):
        rotate = Point.rotate(self.pt2, 90)
        self.assertEqual(rotate.X, 44.592304747138776)
        self.assertEqual(rotate.Y, 100)
        self.assertEqual(rotate.Z, 44.592304747138776)

    def test_mid(self):
        mid = Point.mid(self.pt2, self.pt2)
        self.assertEqual(mid.X, self.pt2.X)
        self.assertEqual(mid.Y, self.pt2.Y)
        self.assertEqual(mid.Z, self.pt2.Z)


if __name__ == '__main__':
    unittest.main()
