import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.point import Point


class test_point(unittest.TestCase):
    """Test for point.py"""
    def setUp(self):
        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(100, 100, 100)
        self.pt3 = Point(150, 130, 200)
        self.pt4 = Point(200, 200, 200)
        self.pt5 = Point(-100, 0, 100)
        self.pt6 = Point(0, 100, 200)
        self.pt7 = Point(-200, -200, -200)
        self.pt8 = Point(-400, -400, -400)
        self.pt9 = Point(-200, -200, -200)
        self.pt10 = Point(200, 200, 200)

    def test_distance_to(self):
        distance = self.pt1.distance_to(self.pt2)
        self.assertEqual(distance, 173.20508075688772)

    def test_angle_to(self):
        angle = self.pt1.angle_to(self.pt2)
        self.assertEqual(angle, 45)

    def test_nearest(self):
        pts = [self.pt2, self.pt3]
        nearest = self.pt1.nearest(pts)
        self.assertEqual(nearest, self.pt2)

    def test_is_same_return_false(self):
        same = self.pt1.is_same(self.pt2)
        self.assertFalse(same)

    def test_is_same_return_true(self):
        same = self.pt1.is_same(self.pt1)
        self.assertTrue(same)

    def test_sub(self):
        sub = self.pt4.sub(self.pt2)
        self.assertEqual(sub.X, self.pt2.X)
        self.assertEqual(sub.Y, self.pt2.Y)
        self.assertEqual(sub.Z, self.pt2.Z)

        subNegative = self.pt7.add(self.pt7)
        self.assertEqual(subNegative.X, self.pt8.X)
        self.assertEqual(subNegative.Y, self.pt8.Y)
        self.assertEqual(subNegative.Z, self.pt8.Z)

    def test_add(self):
        add = self.pt2.add(self.pt2)
        self.assertEqual(add.X, self.pt4.X)
        self.assertEqual(add.Y, self.pt4.Y)
        self.assertEqual(add.Z, self.pt4.Z)

        addNegative = self.pt5.add(self.pt2)
        self.assertEqual(addNegative.X, self.pt6.X)
        self.assertEqual(addNegative.Y, self.pt6.Y)
        self.assertEqual(addNegative.Z, self.pt6.Z)

    def test_multiply(self):
        multiply = self.pt2.multiply(0)
        self.assertEqual(multiply.X, self.pt1.X)
        self.assertEqual(multiply.Y, self.pt1.Y)
        self.assertEqual(multiply.Z, self.pt1.Z)

        multiplyNegative = self.pt7.multiply(1)
        self.assertEqual(multiplyNegative.X, self.pt7.X)
        self.assertEqual(multiplyNegative.Y, self.pt7.Y)
        self.assertEqual(multiplyNegative.Z, self.pt7.Z)

    def test_rotate(self):
        rotate = self.pt2.rotate(90)
        self.assertEqual(rotate.X, 100)
        self.assertEqual(rotate.Y, 100)
        self.assertEqual(rotate.Z, -100)

    def test_mid(self):
        mid = self.pt2.mid(self.pt4)
        self.assertEqual(mid.X, 150)
        self.assertEqual(mid.Y, 150)
        self.assertEqual(mid.Z, 150)

    def test_project(self):
        projected = self.pt1.project(270, 5)
        self.assertEqual(projected.X, self.pt1.X)
        self.assertEqual(projected.Y, self.pt1.Y)
        self.assertEqual(projected.Z, -5)


if __name__ == '__main__':
    unittest.main()
