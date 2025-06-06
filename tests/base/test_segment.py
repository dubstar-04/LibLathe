import os
import sys
import math
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.boundbox import BoundBox

class test_segment(unittest.TestCase):
    """
    Test for segment.py
    To be qualified using model_test_segment.fcstd
    """
    def setUp(self):

        self.Pt1 = Point(0, 10)
        self.Pt2 = Point(4.85643, -8.74157)
        self.Pt3 = Point(9.5, -15.85)
        self.Pt4 = Point(5.4, -22)
        self.Pt5 = Point(5.4, -30)
        self.Pt6 = Point(5.4, -35)

        self.lineSegment1MidPoint = Point(7.17821, -12.29579)

        # arc 1
        # radius: 10, CentrePt: 0, 0, direction: CW
        arc1_start_angle = 0
        arc1_end_angle = -150.94541
        self.arc1_angle = abs(arc1_end_angle - arc1_start_angle)
        self.arc1_bulge = math.tan(math.radians((self.arc1_angle) / 4))

        # arc 2
        # radius: 4.16, CentrePt: 6.54263, -26.00, direction: CCW
        arc2_start_angle = 15.94236
        arc2_end_angle = 164.05762
        self.arc2_angle = -abs(arc2_end_angle - arc2_start_angle)
        self.arc2_bulge = math.tan(math.radians((self.arc2_angle) / 4))

        # large arc
        # radius: 10, CentrePt: 4.85643,1.25843 , direction: CCW
        largeArc_start_angle = -90.00000
        largeArc_end_angle = 119.05460
        self.large_arc_angle = abs(largeArc_end_angle - largeArc_start_angle)
        self.large_arc_bulge = math.tan(math.radians((self.large_arc_angle) / 4))

        # partial arc
        # radius: 5.59017, CentrePt: 1.76777,4.69670 , direction: CCW
        partialArc_start_angle = -18.43495
        partialArc_end_angle = 108.43495
        self.partial_arc_angle = abs(partialArc_end_angle - partialArc_start_angle)
        self.partial_arc_bulge = math.tan(math.radians((self.partial_arc_angle) / 4))

        self.arcSegment1 = Segment(self.Pt1, self.Pt2, self.arc1_bulge)
        self.lineSegment1 = Segment(self.Pt2, self.Pt3)
        self.lineSegment2 = Segment(self.Pt3, self.Pt4)
        self.arcSegment2 = Segment(self.Pt4, self.Pt5, self.arc2_bulge)
        self.largeArcSegment = Segment(self.Pt1, self.Pt2, self.large_arc_bulge)
        self.partialArcSegment = Segment(self.Pt1, Point(7.07107,2.92893), self.partial_arc_bulge)

        # interects line segment 1 at midpoint
        self.lineSegment1Intersect = Segment(Point(3.62400, -14.61757), Point(10.73243, -9.97400))
        # interects arc segment 1
        self.arcSegment1Intersect = Segment(Point(5, 0), Point(12, 0))
        # interects arc segment 2
        self.arcSegment2Intersect = Segment(Point(4.40000, -22.00000), Point(4.40000, -30.00000))

    def test_getAngle(self):
        angle = self.lineSegment1.getAngle()
        self.assertAlmostEqual(angle, math.pi, 5)

        arcAngle = self.arcSegment1.getAngle()
        self.assertAlmostEqual(arcAngle, math.radians(abs(self.arc1_angle)), 5)

    def test_setBulge(self):

        tempSegment = self.lineSegment1
        tempSegment.setBulge(-20)
        self.assertAlmostEqual(tempSegment.bulge, math.tan(-20 / 4), 5)

    def test_getCentrePoint(self):

        lineCentrePt = self.lineSegment1.getCentrePoint()
        centrePt = Point(7.18, -12.295)
        self.assertAlmostEqual(lineCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(lineCentrePt.Z, centrePt.Z, 2)

        arcCentrePt = self.arcSegment1.getCentrePoint()
        centrePt = Point(0.0, 0.0)
        self.assertAlmostEqual(arcCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(arcCentrePt.Z, centrePt.Z, 2)

        arc2CentrePt = self.arcSegment2.getCentrePoint()
        centrePt = Point(6.54, -26.00)
        self.assertAlmostEqual(arc2CentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(arc2CentrePt.Z, centrePt.Z, 2)

        largeArcCentrePt = self.largeArcSegment.getCentrePoint()
        centrePt = Point(4.85643, 1.25843)
        self.assertAlmostEqual(largeArcCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(largeArcCentrePt.Z, centrePt.Z, 2)

        partialArcCentrePt = self.partialArcSegment.getCentrePoint()
        centrePt = Point(1.76777, 4.69670)
        self.assertAlmostEqual(partialArcCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(partialArcCentrePt.Z, centrePt.Z, 2)

    def test_getRadius(self):

        lineRadius = self.lineSegment1.getRadius()
        self.assertEqual(lineRadius, 0)

        arcRadius = self.arcSegment1.getRadius()
        self.assertAlmostEqual(arcRadius, 10, 2)

        arcRadius = self.arcSegment2.getRadius()
        self.assertAlmostEqual(arcRadius, 4.16, 2)

        arcRadius = self.largeArcSegment.getRadius()
        self.assertAlmostEqual(arcRadius, 10, 2)

        arcRadius = self.partialArcSegment.getRadius()
        self.assertAlmostEqual(arcRadius, 5.59017, 2)

    def test_Boundbox(self):

        bb = self.arcSegment1.Boundbox()
        self.assertAlmostEqual(bb.XMin, 0, 2)
        self.assertAlmostEqual(bb.ZMin, -8.74157, 2)
        self.assertAlmostEqual(bb.XMax, 10, 2)
        self.assertAlmostEqual(bb.ZMax, 10, 2)

        bb = self.lineSegment1.Boundbox()
        self.assertAlmostEqual(bb.XMin, 4.85643, 2)
        self.assertAlmostEqual(bb.ZMin, -15.85, 2)
        self.assertAlmostEqual(bb.XMax, 9.5, 2)
        self.assertAlmostEqual(bb.ZMax, -8.74157, 2)

        bb = self.lineSegment2.Boundbox()
        self.assertAlmostEqual(bb.XMin, 5.4, 2)
        self.assertAlmostEqual(bb.ZMin, -22, 2)
        self.assertAlmostEqual(bb.XMax, 9.5, 2)
        self.assertAlmostEqual(bb.ZMax, -15.85, 2)

        bb = self.arcSegment2.Boundbox()
        self.assertAlmostEqual(bb.XMin, 2.38263, 2)
        self.assertAlmostEqual(bb.ZMin, -30, 2)
        self.assertAlmostEqual(bb.XMax, 5.4, 2)
        self.assertAlmostEqual(bb.ZMax,  -22, 2)

        bb = self.largeArcSegment.Boundbox()
        self.assertAlmostEqual(bb.XMin, 0, 2)
        self.assertAlmostEqual(bb.ZMin, -8.74157, 2)
        self.assertAlmostEqual(bb.XMax, 14.8564, 2)
        self.assertAlmostEqual(bb.ZMax,  11.2584, 2)

        bb = self.partialArcSegment.Boundbox()
        self.assertAlmostEqual(bb.XMin, 0, 2)
        self.assertAlmostEqual(bb.ZMin, 2.92893, 2)
        self.assertAlmostEqual(bb.XMax, 7.35794, 2)
        self.assertAlmostEqual(bb.ZMax, 10.2869, 2)

    def test_getRotation(self):

        angle = self.lineSegment1.getRotation()
        self.assertAlmostEqual(angle, math.radians(213.15452), 2)

        angle = self.lineSegment2.getRotation()
        self.assertAlmostEqual(angle, math.radians(146.30993), 2)

    def test_getLength(self):

        length = self.lineSegment1.getLength()
        self.assertAlmostEqual(length, 8.49073, 5)

        arcSegmentLength = self.arcSegment1.getLength()
        self.assertAlmostEqual(arcSegmentLength, 19.36056, 5)

    def test_getEta(self):
        eta = self.lineSegment1.getEta()
        self.assertAlmostEqual(eta, math.pi / 2, 5)

        arcEta = self.arcSegment1.getEta()
        self.assertAlmostEqual(arcEta, abs(math.radians(self.arc1_angle / 2)), 5)

    def test_getEpsilon(self):
        epsilon = self.lineSegment1.getEpsilon()
        self.assertEqual(epsilon, 0)

        arcEpsilon = self.arcSegment1.getEpsilon()
        self.assertAlmostEqual(arcEpsilon, abs(math.radians(self.arc1_angle / 4)), 5)

    def test_getPhi(self):
        phi = self.lineSegment1.getPhi()
        self.assertEqual(phi, 0)

        arcPhi = self.arcSegment1.getPhi()
        self.assertAlmostEqual(arcPhi, 0.91217, 5)

    def test_isSame(self):
        lineComparison = self.lineSegment1.isSame(self.lineSegment1)
        self.assertTrue(lineComparison)

        arcComparison = self.arcSegment1.isSame(self.arcSegment1)
        self.assertTrue(arcComparison)

        lineArcComparison = self.lineSegment1.isSame(self.arcSegment1)
        self.assertFalse(lineArcComparison)

    def test_intersect(self):
        # Line Intersections
        # intersection: 1
        pts = self.lineSegment1.intersect(self.lineSegment1Intersect)
        pt = pts[0]
        self.assertTrue(len(pts) > 0)
        self.assertAlmostEqual(pt.X, self.lineSegment1MidPoint.X, 4)
        self.assertAlmostEqual(pt.Z, self.lineSegment1MidPoint.Z, 4)

        # intersection: 1 - extend
        pts = self.lineSegment2.intersect(self.lineSegment1Intersect, True)
        pt = pts[0]
        intersectExtend = Point(15.48867, -6.86699)
        self.assertTrue(len(pts) > 0)
        self.assertAlmostEqual(pt.X, intersectExtend.X, 4)
        self.assertAlmostEqual(pt.Z, intersectExtend.Z, 4)

        # no intersection
        pts = self.lineSegment2.intersect(self.lineSegment1Intersect, False)
        self.assertTrue(len(pts) == 0)

        #Arc Intersections
        # intersection: 1
        pts = self.arcSegment1.intersect(self.arcSegment1Intersect)
        pt = pts[0]
        self.assertTrue(len(pts) == 1)
        self.assertAlmostEqual(pt.X, 10, 4)
        self.assertAlmostEqual(pt.Z, 0, 4)

        # intersection 2
        pts = self.arcSegment2.intersect(self.arcSegment2Intersect)
        self.assertEqual(len(pts), 2)

        pt = pts[0]
        self.assertAlmostEqual(pt.X, 4.4, 4)
        self.assertAlmostEqual(pt.Z, -29.56578, 4)

        pt = pts[1]
        self.assertAlmostEqual(pt.X, 4.4, 4)
        self.assertAlmostEqual(pt.Z, -22.43422, 4)

        # intersection: 2 - extend
        pts = self.arcSegment1.intersect(self.arcSegment2Intersect, True)
        self.assertTrue(len(pts) == 2)

        pt = pts[0]
        self.assertAlmostEqual(pt.X, 4.4, 4)
        self.assertAlmostEqual(pt.Z, -8.97997, 4)

        pt = pts[1]
        self.assertAlmostEqual(pt.X, 4.4, 4)
        self.assertAlmostEqual(pt.Z, 8.97997, 4)

        # no intersection
        pts = self.arcSegment1.intersect(self.arcSegment2Intersect)
        self.assertTrue(len(pts) == 0)

    def test_pointOnSegment(self):
        # Line Segments
        # mid point
        point = self.lineSegment1MidPoint
        on_seg = self.lineSegment1.pointOnSegment(point)
        self.assertTrue(on_seg)

        # start
        point = self.Pt2
        on_seg = self.lineSegment1.pointOnSegment(point)
        self.assertTrue(on_seg)

        # end
        point = self.Pt3
        on_seg = self.lineSegment1.pointOnSegment(point)
        self.assertTrue(on_seg)

        # offline
        point = self.Pt1
        on_seg = self.lineSegment1.pointOnSegment(point)
        self.assertFalse(on_seg)

        # Arc Segments
        # center point
        point = Point()
        on_seg = self.arcSegment1.pointOnSegment(point)
        self.assertFalse(on_seg)

        # start point
        point = self.Pt1
        on_seg = self.arcSegment1.pointOnSegment(point)
        self.assertTrue(on_seg)

        # end point
        point = self.Pt2
        on_seg = self.arcSegment1.pointOnSegment(point)
        self.assertTrue(on_seg)

        # Arc segment 2
        point = Point(4.4, -29.5658)
        on_seg = self.arcSegment2.pointOnSegment(point)
        self.assertTrue(on_seg)

        point = Point(4.4, -22.4342)
        on_seg = self.arcSegment2.pointOnSegment(point)
        self.assertTrue(on_seg)

    def test_distanceToPoint(self):

        point = Point(10.73243, -9.97400)
        dist = self.lineSegment1.distanceToPoint(point)
        self.assertAlmostEqual(dist, 4.24536, 4)

        # TODO: remove this test when the arc support is removed from segement
        dist = self.arcSegment1.distanceToPoint(point)
        self.assertAlmostEqual(dist, 4.65147, 4)

    def test_closestPoint(self):

        """
        # Arcs not supported
        point = Point(12, 0)
        closest = self.arcSegment1.closestPoint(point)
        self.assertAlmostEqual(closest.X, self.lineSegment1MidPoint.X, 4)
        self.assertAlmostEqual(closest.Z, self.lineSegment1MidPoint.Z, 4)
        """

        # closest start segment
        point = Point(3, -7.5)
        closest = self.lineSegment1.closestPoint(point)
        self.assertAlmostEqual(closest.X, self.lineSegment1.start.X, 4)
        self.assertAlmostEqual(closest.Z, self.lineSegment1.start.Z, 4)

        # closest mid segment
        point = self.lineSegment1Intersect.start
        closest = self.lineSegment1.closestPoint(point)
        self.assertAlmostEqual(closest.X, self.lineSegment1MidPoint.X, 4)
        self.assertAlmostEqual(closest.Z, self.lineSegment1MidPoint.Z, 4)

        # closest end segment
        point = self.lineSegment2.getCentrePoint()
        closest = self.lineSegment1.closestPoint(point)
        self.assertAlmostEqual(closest.X, self.lineSegment1.end.X, 4)
        self.assertAlmostEqual(closest.Z, self.lineSegment1.end.Z, 4)





if __name__ == '__main__':
    unittest.main()
