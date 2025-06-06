import os
import sys
import unittest
import math

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.point import Point


class test_point(unittest.TestCase):
    """Test for point.py"""
    def setUp(self):
        self.pt1 = Point(0, 0)
        self.pt2 = Point(100, 100)
        self.pt3 = Point(150, 200)
        self.pt4 = Point(200, 200)
        self.pt5 = Point(-100, 100)
        self.pt6 = Point(0, 200)
        self.pt7 = Point(-200, -200)
        self.pt8 = Point(-400, -400)
        self.pt9 = Point(-200, -200)
        self.pt10 = Point(200, 200)

    def test_distanceTo(self):
        distance = self.pt1.distanceTo(self.pt2)
        self.assertAlmostEqual(distance, 141.421356, 5)

    def test_angleTo(self):

        angle = self.pt1.angleTo(Point(0, 100))
        self.assertEqual(angle, 0)

        angle = self.pt1.angleTo(Point(100, 100))
        self.assertAlmostEqual(angle, math.radians(315), 5)

        angle = self.pt1.angleTo(Point(100, 0))
        self.assertAlmostEqual(angle, math.radians(270), 5)

        angle = self.pt1.angleTo(Point(100, -100))
        self.assertAlmostEqual(angle, math.radians(225), 5)

        angle = self.pt1.angleTo(Point(0, -100))
        self.assertAlmostEqual(angle, math.radians(180), 5)

        angle = self.pt1.angleTo(Point(-100, -100))
        self.assertAlmostEqual(angle, math.radians(135), 5)

        angle = self.pt1.angleTo(Point(-100, 0))
        self.assertAlmostEqual(angle, math.radians(90), 5)

        angle = self.pt1.angleTo(Point(-100, 100))
        self.assertAlmostEqual(angle, math.radians(45), 5)

        angle = self.pt1.angleTo(Point(-100, -100))
        self.assertAlmostEqual(angle, math.radians(135), 5)


    def test_nearest(self):
        pts = [self.pt2, self.pt3]
        nearest = self.pt1.nearest(pts)
        self.assertEqual(nearest.X, self.pt2.X)
        self.assertEqual(nearest.Z, self.pt2.Z)

    def test_isSame_return_false(self):
        same = self.pt1.isSame(self.pt2)
        self.assertFalse(same)

    def test_isSame_return_true(self):
        same = self.pt1.isSame(self.pt1)
        self.assertTrue(same)

    def test_sub(self):
        sub = self.pt4.sub(self.pt2)
        self.assertEqual(sub.X, self.pt2.X)
        #self.assertEqual(sub.Y, self.pt2.Y)
        self.assertEqual(sub.Z, self.pt2.Z)

        subNegative = self.pt7.add(self.pt7)
        self.assertEqual(subNegative.X, self.pt8.X)
        #self.assertEqual(subNegative.Y, self.pt8.Y)
        self.assertEqual(subNegative.Z, self.pt8.Z)

    def test_add(self):
        add = self.pt2.add(self.pt2)
        self.assertEqual(add.X, self.pt4.X)
        #self.assertEqual(add.Y, self.pt4.Y)
        self.assertEqual(add.Z, self.pt4.Z)

        addNegative = self.pt5.add(self.pt2)
        self.assertEqual(addNegative.X, self.pt6.X)
        #self.assertEqual(addNegative.Y, self.pt6.Y)
        self.assertEqual(addNegative.Z, self.pt6.Z)

    def test_multiply(self):
        multiply = self.pt2.multiply(0)
        self.assertEqual(multiply.X, self.pt1.X)
        #self.assertEqual(multiply.Y, self.pt1.Y)
        self.assertEqual(multiply.Z, self.pt1.Z)

        multiplyNegative = self.pt7.multiply(1)
        self.assertEqual(multiplyNegative.X, self.pt7.X)
        #self.assertEqual(multiplyNegative.Y, self.pt7.Y)
        self.assertEqual(multiplyNegative.Z, self.pt7.Z)

    def test_lerp(self):
        lerp = self.pt1.lerp(self.pt2, 0.5)
        self.assertEqual(lerp.X, 50)
        #self.assertEqual(lerp.Y, 50)
        self.assertEqual(lerp.Z, 50)

    def test_normaliseTo(self):
        normal = self.pt1.normaliseTo(Point(100, 100))
        self.assertAlmostEqual(normal.X, 0.7071067811865475, 5)
        #self.assertEqual(normal.Y, 0)
        self.assertAlmostEqual(normal.Z, 0.7071067811865475, 5)

        normal = self.pt1.normaliseTo(self.pt1)
        self.assertEqual(normal.X, 0)
        #self.assertEqual(normal.Y, 0)
        self.assertEqual(normal.Z, 0)

    def test_rotate(self):
        rotate = self.pt6.rotate(Point(), math.radians(45))
        self.assertAlmostEqual(rotate.X, -141.421356, 4)
        self.assertAlmostEqual(rotate.Z, 141.421356, 4)

        rotate = self.pt6.rotate(Point(), math.radians(90))
        self.assertAlmostEqual(rotate.X, -200, 4)
        self.assertAlmostEqual(rotate.Z, 0, 4)

        rotate = self.pt6.rotate(Point(), math.radians(180))
        self.assertAlmostEqual(rotate.X, 0, 4)
        self.assertAlmostEqual(rotate.Z, -200, 4)

        rotate = self.pt6.rotate(Point(), math.radians(270))
        self.assertAlmostEqual(rotate.X, 200, 4)
        self.assertAlmostEqual(rotate.Z, 0, 4)

        rotate = self.pt2.rotate(Point(), math.radians(90))
        self.assertAlmostEqual(rotate.X, -100, 4)
        self.assertAlmostEqual(rotate.Z, 100, 4)

        rotate = self.pt4.rotate(self.pt2, math.radians(-90))
        self.assertAlmostEqual(rotate.X, 200, 4)
        self.assertAlmostEqual(rotate.Z, 0, 4)

    def test_mid(self):
        mid = self.pt2.mid(self.pt4)
        self.assertEqual(mid.X, 150)
        self.assertEqual(mid.Z, 150)

    def test_project(self):
        projected = self.pt1.project(0, 5)
        self.assertEqual(projected.X, 0)
        self.assertEqual(projected.Z, 5)

        projected = self.pt1.project(math.radians(45), 5)
        self.assertAlmostEqual(projected.X, -3.53553, 5)
        self.assertAlmostEqual(projected.Z, 3.53553, 5)

        projected = self.pt1.project(math.radians(90), 5)
        self.assertAlmostEqual(projected.X, -5, 5)
        self.assertAlmostEqual(projected.Z, 0, 5)

        projected = self.pt1.project(math.radians(135), 5)
        self.assertAlmostEqual(projected.X, -3.53553, 5)
        self.assertAlmostEqual(projected.Z, -3.53553, 5)

        projected = self.pt1.project(math.radians(180), 5)
        self.assertAlmostEqual(projected.X, 0, 5)
        self.assertAlmostEqual(projected.Z, -5, 5)

        projected = self.pt1.project(math.radians(225), 5)
        self.assertAlmostEqual(projected.X, 3.53553, 5)
        self.assertAlmostEqual(projected.Z, -3.53553, 5)

        projected = self.pt1.project(math.radians(270), 5)
        self.assertAlmostEqual(projected.X, 5, 5)
        self.assertAlmostEqual(projected.Z, 0, 5)


if __name__ == '__main__':
    unittest.main()
