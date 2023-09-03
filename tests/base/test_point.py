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

    def test_distance_to(self):
        distance = self.pt1.distance_to(self.pt2)
        self.assertAlmostEqual(distance, 141.421356, 5)

    def test_angle_to(self):

        angle = self.pt1.angle_to(Point(0, 100))
        self.assertEqual(angle, 0)

        angle = self.pt1.angle_to(Point(100, 100))
        self.assertAlmostEqual(angle, math.radians(315), 5)

        angle = self.pt1.angle_to(Point(100, 0))
        self.assertAlmostEqual(angle, math.radians(270), 5)

        angle = self.pt1.angle_to(Point(100, -100))
        self.assertAlmostEqual(angle, math.radians(225), 5)

        angle = self.pt1.angle_to(Point(0, -100))
        self.assertAlmostEqual(angle, math.radians(180), 5)

        angle = self.pt1.angle_to(Point(-100, -100))
        self.assertAlmostEqual(angle, math.radians(135), 5)

        angle = self.pt1.angle_to(Point(-100, 0))
        self.assertAlmostEqual(angle, math.radians(90), 5)

        angle = self.pt1.angle_to(Point(-100, 100))
        self.assertAlmostEqual(angle, math.radians(45), 5)

        angle = self.pt1.angle_to(Point(-100, -100))
        self.assertAlmostEqual(angle, math.radians(135), 5)


    def test_nearest(self):
        pts = [self.pt2, self.pt3]
        nearest = self.pt1.nearest(pts)
        self.assertEqual(nearest.x, self.pt2.x)
        self.assertEqual(nearest.z, self.pt2.z)

    def test_is_same_return_false(self):
        same = self.pt1.is_same(self.pt2)
        self.assertFalse(same)

    def test_is_same_return_true(self):
        same = self.pt1.is_same(self.pt1)
        self.assertTrue(same)

    def test_sub(self):
        sub = self.pt4.sub(self.pt2)
        self.assertEqual(sub.x, self.pt2.x)
        #self.assertEqual(sub.Y, self.pt2.Y)
        self.assertEqual(sub.z, self.pt2.z)

        subNegative = self.pt7.add(self.pt7)
        self.assertEqual(subNegative.x, self.pt8.x)
        #self.assertEqual(subNegative.Y, self.pt8.Y)
        self.assertEqual(subNegative.z, self.pt8.z)

    def test_add(self):
        add = self.pt2.add(self.pt2)
        self.assertEqual(add.x, self.pt4.x)
        #self.assertEqual(add.Y, self.pt4.Y)
        self.assertEqual(add.z, self.pt4.z)

        addNegative = self.pt5.add(self.pt2)
        self.assertEqual(addNegative.x, self.pt6.x)
        #self.assertEqual(addNegative.Y, self.pt6.Y)
        self.assertEqual(addNegative.z, self.pt6.z)

    def test_multiply(self):
        multiply = self.pt2.multiply(0)
        self.assertEqual(multiply.x, self.pt1.x)
        #self.assertEqual(multiply.Y, self.pt1.Y)
        self.assertEqual(multiply.z, self.pt1.z)

        multiplyNegative = self.pt7.multiply(1)
        self.assertEqual(multiplyNegative.x, self.pt7.x)
        #self.assertEqual(multiplyNegative.Y, self.pt7.Y)
        self.assertEqual(multiplyNegative.z, self.pt7.z)

    def test_lerp(self):
        lerp = self.pt1.lerp(self.pt2, 0.5)
        self.assertEqual(lerp.x, 50)
        #self.assertEqual(lerp.Y, 50)
        self.assertEqual(lerp.z, 50)

    def test_normalise_to(self):
        normal = self.pt1.normalise_to(Point(100, 100))
        self.assertAlmostEqual(normal.x, 0.7071067811865475, 5)
        #self.assertEqual(normal.Y, 0)
        self.assertAlmostEqual(normal.z, 0.7071067811865475, 5)

        normal = self.pt1.normalise_to(self.pt1)
        self.assertEqual(normal.x, 0)
        #self.assertEqual(normal.Y, 0)
        self.assertEqual(normal.z, 0)

    def test_rotate(self):
        rotate = self.pt6.rotate(Point(), math.radians(45))
        self.assertAlmostEqual(rotate.x, -141.421356, 4)
        self.assertAlmostEqual(rotate.z, 141.421356, 4)
    
        rotate = self.pt6.rotate(Point(), math.radians(90))
        self.assertAlmostEqual(rotate.x, -200, 4)
        self.assertAlmostEqual(rotate.z, 0, 4)

        rotate = self.pt6.rotate(Point(), math.radians(180))
        self.assertAlmostEqual(rotate.x, 0, 4)
        self.assertAlmostEqual(rotate.z, -200, 4)

        rotate = self.pt6.rotate(Point(), math.radians(270))
        self.assertAlmostEqual(rotate.x, 200, 4)
        self.assertAlmostEqual(rotate.z, 0, 4)

        rotate = self.pt2.rotate(Point(), math.radians(90))
        self.assertAlmostEqual(rotate.x, -100, 4)
        self.assertAlmostEqual(rotate.z, 100, 4)

        rotate = self.pt4.rotate(self.pt2, math.radians(-90))
        self.assertAlmostEqual(rotate.x, 200, 4)
        self.assertAlmostEqual(rotate.z, 0, 4)

    def test_mid(self):
        mid = self.pt2.mid(self.pt4)
        self.assertEqual(mid.x, 150)
        self.assertEqual(mid.z, 150)

    def test_project(self):
        projected = self.pt1.project(0, 5)
        self.assertEqual(projected.x, 0)
        self.assertEqual(projected.z, 5)

        projected = self.pt1.project(math.radians(45), 5)
        self.assertAlmostEqual(projected.x, -3.53553, 5)
        self.assertAlmostEqual(projected.z, 3.53553, 5)

        projected = self.pt1.project(math.radians(90), 5)
        self.assertAlmostEqual(projected.x, -5, 5)
        self.assertAlmostEqual(projected.z, 0, 5)

        projected = self.pt1.project(math.radians(135), 5)
        self.assertAlmostEqual(projected.x, -3.53553, 5)
        self.assertAlmostEqual(projected.z, -3.53553, 5)

        projected = self.pt1.project(math.radians(180), 5)
        self.assertAlmostEqual(projected.x, 0, 5)
        self.assertAlmostEqual(projected.z, -5, 5)

        projected = self.pt1.project(math.radians(225), 5)
        self.assertAlmostEqual(projected.x, 3.53553, 5)
        self.assertAlmostEqual(projected.z, -3.53553, 5)

        projected = self.pt1.project(math.radians(270), 5)
        self.assertAlmostEqual(projected.x, 5, 5)
        self.assertAlmostEqual(projected.z, 0, 5)


if __name__ == '__main__':
    unittest.main()
