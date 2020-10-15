import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(os.path.dirname(thisFolder))
sys.path.append(parentFolder)
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment


class test_segment(unittest.TestCase):
    """Test for LLSegment.py"""
    def setUp(self):
        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(100, 0, 100)
        self.pt3 = Point(100, 0, 0)
        self.pt4 = Point(0, 0, 100)

        self.lineSegment = Segment(self.pt1, self.pt2)
        self.inverseLineSegment = Segment(self.pt3, self.pt4)
        self.arcSegment = Segment(self.pt1, self.pt2, 1.5)
        self.inverseArcSegment = Segment(self.pt2, self.pt1, 1.5)

    def test_get_angle(self):
        angle = self.lineSegment.get_angle()
        self.assertEqual(angle, 180)

        arcAngle = self.arcSegment.get_angle()
        self.assertEqual(arcAngle, 3.931174892989316)

    def test_get_centre_point(self):
        lineCentrePt = self.lineSegment.get_centre_point()
        self.assertEqual(lineCentrePt, None)

        arcCentrePt = self.arcSegment.get_centre_point()
        centrePt = Point(6.399063465715933, 0.0, 93.60093653428407)
        self.assertTrue(arcCentrePt.is_same(centrePt))

        invArcCenPt = self.inverseArcSegment.get_centre_point()
        centrePt = Point(93.60093653428407, 0.0, 6.399063465715933)
        self.assertTrue(invArcCenPt.is_same(centrePt))

    def test_get_radius(self):
        lineRadius = self.lineSegment.get_radius()
        self.assertEqual(lineRadius, 0)

        arcRadius = self.arcSegment.get_radius()
        self.assertEqual(arcRadius, 76.60323462854265)

    def test_get_length(self):
        length = self.lineSegment.get_length()
        self.assertEqual(length, 141.4213562373095)

        arcSegmentLength = self.arcSegment.get_length()
        self.assertEqual(arcSegmentLength, 141.4213562373095)

    def test_get_eta(self):
        eta = self.lineSegment.get_eta()
        self.assertEqual(eta, 90)

        arcEta = self.arcSegment.get_eta()
        self.assertEqual(arcEta, 1.965587446494658)

    def test_get_epsilon(self):
        epsilon = self.lineSegment.get_epsilon()
        self.assertEqual(epsilon, 0)

        arcEpsilon = self.arcSegment.get_epsilon()
        self.assertEqual(arcEpsilon, 0.982793723247329)

    def test_is_same(self):
        lineComparison = self.lineSegment.is_same(self.lineSegment)
        self.assertTrue(lineComparison)

        arcComparison = self.arcSegment.is_same(self.arcSegment)
        self.assertTrue(arcComparison)

        lineArcComparison = self.lineSegment.is_same(self.arcSegment)
        self.assertFalse(lineArcComparison)

    def test_intersect(self):
        intersect, pt = self.lineSegment.intersect(self.inverseLineSegment)
        print("intersect", intersect, pt.X, pt.Y, pt.Z)
        self.assertTrue(intersect)
        intersectionPt = Point(50, 0.0, 50)
        self.assertTrue(pt.is_same(intersectionPt))


if __name__ == '__main__':
    unittest.main()
