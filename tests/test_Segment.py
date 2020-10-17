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
        self.inverseArcSegment = Segment(self.pt1, self.pt2, -1.5)

    def test_get_angle(self):
        angle = self.lineSegment.get_angle()
        self.assertEqual(angle, 180)

        arcAngle = self.arcSegment.get_angle()
        self.assertEqual(arcAngle, 3.931174892989316)

    def test_get_centre_point(self):
        lineCentrePt = self.lineSegment.get_centre_point()
        self.assertEqual(lineCentrePt, None)

        arcCentrePt = self.arcSegment.get_centre_point()
        #print('arcCentrePt', arcCentrePt.X, arcCentrePt.Y, arcCentrePt.Z)
        centrePt = Point(70.83333333333333, 0.0, 29.166666666666668)
        self.assertTrue(arcCentrePt.is_same(centrePt))

        invArcCenPt = self.inverseArcSegment.get_centre_point()
        # TODO: Investigate bulge direction errors
        # print('invArcCenPt', invArcCenPt.X, invArcCenPt.Y, invArcCenPt.Z)
        centrePt = Point(29.166666666666668, 0.0, 70.83333333333333)
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
        self.assertTrue(intersect)
        intersectionPt = Point(50, 0.0, 50)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.arcSegment.intersect(self.inverseLineSegment)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(16.666666666666657, 0.0, 83.33333333333334)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.inverseArcSegment.intersect(self.inverseLineSegment)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(83.33333333333334, 0.0, 16.66666666666666)
        self.assertTrue(pt.is_same(intersectionPt))

        self.pt5 = Point(-120.12, 0, 214.09)
        self.pt6 = Point(-179.88, 0, 85.91)
        self.pt7 = Point(-214.09, 0, 179.88)
        self.pt8 = Point(-85.91, 0, 120.12)

        self.lineSegment = Segment(self.pt5, self.pt6)
        self.arcSegment = Segment(self.pt7, self.pt8, 1.5)
        self.inverseArcSegment = Segment(self.pt7, self.pt8, -1.5)

        intersect, pts = self.arcSegment.intersect(self.lineSegment)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(-130.08000000000004, 0.0, 192.72666666666657)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.inverseArcSegment.intersect(self.lineSegment)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(-169.91999999999996, 0.0, 107.27333333333338)
        self.assertTrue(pt.is_same(intersectionPt))

        # false intersection tests
        self.lineSegment = Segment(self.pt1, self.pt2)

        intersect, pts = self.inverseArcSegment.intersect(self.lineSegment)
        self.assertFalse(intersect)

        self.pt9 = Point(-164.74, 0, 118.39)
        self.pt10 = Point(-137.55, 0, 176.70)
        self.lineSegment = Segment(self.pt9, self.pt10)

        intersect, pts = self.arcSegment.intersect(self.lineSegment)
        self.assertFalse(intersect)


if __name__ == '__main__':
    unittest.main()
