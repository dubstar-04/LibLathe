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
        self.pt5 = Point(-120.12, 0, 214.09)
        self.pt6 = Point(-179.88, 0, 85.91)
        self.pt7 = Point(-214.09, 0, 179.88)
        self.pt8 = Point(-85.91, 0, 120.12)
        self.pt9 = Point(-164.74, 0, 118.39)
        self.pt10 = Point(-137.55, 0, 176.70)

        self.lineSegment1 = Segment(self.pt1, self.pt2)
        self.lineSegment2 = Segment(self.pt5, self.pt6)
        self.lineSegment3 = Segment(self.pt9, self.pt10)

        self.inverseLineSegment1 = Segment(self.pt3, self.pt4)

        self.arcSegment1 = Segment(self.pt1, self.pt2, 1.5)
        self.arcSegment2 = Segment(self.pt7, self.pt8, 1.5)

        self.inverseArcSegment1 = Segment(self.pt1, self.pt2, -1.5)
        self.inverseArcSegment2 = Segment(self.pt7, self.pt8, -1.5)

    def test_get_angle(self):
        angle = self.lineSegment1.get_angle()
        self.assertEqual(angle, 180)

        arcAngle = self.arcSegment1.get_angle()
        self.assertEqual(arcAngle, 3.931174892989316)

    def test_set_bulge(self):
        tempSegment = self.lineSegment1
        tempSegment.set_bulge(3.931174892989316)
        self.assertEqual(tempSegment.bulge, 1.5)

    def test_set_bulge_from_radius(self):
        tempSegment = self.lineSegment1
        tempSegment.set_bulge_from_radius(76.60323462854265)
        self.assertEqual(tempSegment.bulge, 0.6666666666666667)

    def test_get_centre_point(self):
        lineCentrePt = self.lineSegment1.get_centre_point()
        self.assertEqual(lineCentrePt, None)

        arcCentrePt = self.arcSegment1.get_centre_point()
        centrePt = Point(70.83333333333333, 0.0, 29.166666666666668)
        self.assertTrue(arcCentrePt.is_same(centrePt))

        invArcCenPt = self.inverseArcSegment1.get_centre_point()
        centrePt = Point(29.166666666666668, 0.0, 70.83333333333333)
        self.assertTrue(invArcCenPt.is_same(centrePt))

    def test_get_radius(self):
        lineRadius = self.lineSegment1.get_radius()
        self.assertEqual(lineRadius, 0)

        arcRadius = self.arcSegment1.get_radius()
        self.assertEqual(arcRadius, 76.60323462854265)

    def test_get_extent_min(self):
        extentMinX = self.lineSegment2.get_extent_min('X')
        self.assertEqual(extentMinX, self.pt5.X)

        extentMinY = self.lineSegment2.get_extent_min('Y')
        self.assertEqual(extentMinY, self.pt5.Y)

        extentMinZ = self.lineSegment2.get_extent_min('Z')
        self.assertEqual(extentMinZ, self.pt6.Z)

        AecExtentMinX = self.arcSegment2.get_extent_min('X')
        self.assertEqual(AecExtentMinX, self.pt8.X)

        AecExtentMinY = self.arcSegment2.get_extent_min('Y')
        self.assertEqual(AecExtentMinY, self.pt5.Y)

        AecExtentMinZ = self.arcSegment2.get_extent_min('Z')
        self.assertEqual(AecExtentMinZ, 46.68997508893331)

    def test_get_extent_max(self):
        extentMaxX = self.lineSegment2.get_extent_max('X')
        self.assertEqual(extentMaxX, self.pt6.X)

        extentMaxY = self.lineSegment2.get_extent_max('Y')
        self.assertEqual(extentMaxY, self.pt5.Y)

        extentMaxZ = self.lineSegment2.get_extent_max('Z')
        self.assertEqual(extentMaxZ, self.pt5.Z)

        AecExtentMaxX = self.arcSegment2.get_extent_max('X')
        self.assertEqual(AecExtentMaxX, -239.0558582444)

        AecExtentMaxY = self.arcSegment2.get_extent_max('Y')
        self.assertEqual(AecExtentMaxY, -76.60585824440003)

        AecExtentMaxZ = self.arcSegment2.get_extent_max('Z')
        self.assertEqual(AecExtentMaxZ, self.pt7.Z)

    def test_get_all_axis_positions(self):
        allAxisPosX = self.lineSegment2.get_all_axis_positions('X')
        self.assertEqual(allAxisPosX, [self.pt5.X, self.pt6.X])

        allAxisPosY = self.lineSegment2.get_all_axis_positions('Y')
        self.assertEqual(allAxisPosY, [self.pt5.Y, self.pt6.Y])

        allAxisPosZ = self.lineSegment2.get_all_axis_positions('Z')
        self.assertEqual(allAxisPosZ, [self.pt5.Z, self.pt6.Z])

        arcAllAxisPosX = self.arcSegment2.get_all_axis_positions('X')
        self.assertEqual(arcAllAxisPosX, [self.pt7.X, self.pt8.X, -239.0558582444])

        arcAllAxisPosY = self.arcSegment2.get_all_axis_positions('Y')
        self.assertEqual(arcAllAxisPosY, [self.pt7.Y, self.pt8.Y, -76.60585824440003])

        arcAllAxisPosZ = self.arcSegment2.get_all_axis_positions('Z')
        self.assertEqual(arcAllAxisPosZ, [self.pt7.Z, self.pt8.Z, 46.68997508893331])

    def test_get_length(self):
        length = self.lineSegment1.get_length()
        self.assertEqual(length, 141.4213562373095)

        arcSegmentLength = self.arcSegment1.get_length()
        self.assertEqual(arcSegmentLength, 141.4213562373095)

    def test_get_eta(self):
        eta = self.lineSegment1.get_eta()
        self.assertEqual(eta, 90)

        arcEta = self.arcSegment1.get_eta()
        self.assertEqual(arcEta, 1.965587446494658)

    def test_get_epsilon(self):
        epsilon = self.lineSegment1.get_epsilon()
        self.assertEqual(epsilon, 0)

        arcEpsilon = self.arcSegment1.get_epsilon()
        self.assertEqual(arcEpsilon, 0.982793723247329)

    def test_get_phi(self):
        phi = self.lineSegment1.get_phi()
        self.assertEqual(phi, -88.42920367320511)

        arcPhi = self.arcSegment1.get_phi()
        self.assertEqual(arcPhi, 0.5880026035475675)

    def test_is_same(self):
        lineComparison = self.lineSegment1.is_same(self.lineSegment1)
        self.assertTrue(lineComparison)

        arcComparison = self.arcSegment1.is_same(self.arcSegment1)
        self.assertTrue(arcComparison)

        lineArcComparison = self.lineSegment1.is_same(self.arcSegment1)
        self.assertFalse(lineArcComparison)

    def test_intersect(self):

        intersect, pt = self.lineSegment1.intersect(self.inverseLineSegment1)
        self.assertTrue(intersect)
        intersectionPt = Point(50, 0.0, 50)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.arcSegment1.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(16.666666666666657, 0.0, 83.33333333333334)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.inverseArcSegment1.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(83.33333333333334, 0.0, 16.66666666666666)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.arcSegment2.intersect(self.lineSegment2)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(-130.08000000000004, 0.0, 192.72666666666657)
        self.assertTrue(pt.is_same(intersectionPt))

        intersect, pts = self.inverseArcSegment2.intersect(self.lineSegment2)
        pt = pts[0]
        self.assertTrue(intersect)
        intersectionPt = Point(-169.91999999999996, 0.0, 107.27333333333338)
        self.assertTrue(pt.is_same(intersectionPt))

        # false intersection tests
        intersect, pts = self.inverseArcSegment2.intersect(self.lineSegment1)
        self.assertFalse(intersect)

        intersect, pts = self.arcSegment2.intersect(self.lineSegment3)
        self.assertFalse(intersect)


if __name__ == '__main__':
    unittest.main()
