import os
from re import A
import sys
import math
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup

if 'PIL' in sys.modules:
    from liblathe.plot import Plot

#TODO: evaluate errors where AlmostEqual tests are to <5 decimal places, note coordinate input is only to 2 decimal places


class test_segment(unittest.TestCase):
    """
    Test for segment.py
    To be qualified using model_test_segment.fcstd
    """
    def setUp(self):
        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(-53.03, 0, -128.03)
        self.pt3 = Point(-193.47, 0, 5.14)
        self.pt4 = Point(37.5, 0, -90.53)
        self.pt5 = Point(-53.03, 0, -128.03)
        self.pt6 = Point(-88.39, 0, -163.39)
        self.pt7 = Point(-88.388, 0, -177.86)
        self.pt8 = Point(-88.388, 0, -222.14)
        self.pt9 = Point(0, 0,0 -100) # partial arc center
        self.pt10 = Point(-42.26,  0,  -9.37,) # partial arc end

        self.lineSegment1 = Segment(self.pt1, self.pt2)
        self.lineSegment2 = Segment(self.pt5, self.pt6)
        self.lineSegment3= Segment(self.pt6, self.pt7)
        self.inverseLineSegment1 = Segment(self.pt3, self.pt4)

        # start and end angles taken from model_test_segment.fcstd
        arc1_start_angle = 90
        arc1_end_angle = 225
        
        arc2_start_angle = 27.68
        arc2_end_angle = 152.32

        large_arc_start_angle = -202.5
        large_arc_end_angle = 67.5

        partial_arc_start_angle = -25
        partial_arc_end_angle = 0

        self.arc1_angle = -abs(arc1_end_angle - arc1_start_angle) 
        self.arc2_angle = abs(arc2_end_angle - arc2_start_angle) 
        self.large_arc_angle = -abs(large_arc_end_angle - large_arc_start_angle)
        self.partial_arc_angle = -abs(partial_arc_end_angle - partial_arc_start_angle)  
        
        self.arc1_bulge = math.tan(math.radians((self.arc1_angle) / 4))  # radius: 75, CentrePt: 0, -75, direction: CW
        self.arc2_bulge = math.tan(math.radians((self.arc2_angle) / 4))  # radius: 25, CentrePt: 100, -100, direction: CCW
        self.large_arc_bulge = math.tan(math.radians((self.large_arc_angle) / 4))  # radius: 97.99, CentrePt: self.pt3, direction: CW
        self.partial_arc_bulge = math.tan(math.radians((self.partial_arc_angle) / 4))  # radius: 100, CentrePt: self.pt9, direction: CW

        self.arcSegment1 = Segment(self.pt1, self.pt2, self.arc1_bulge)    
        self.arcSegment2 = Segment(self.pt7, self.pt8, self.arc2_bulge)
        self.largeArcSegment = Segment(self.pt1, self.pt2, self.large_arc_bulge)
        self.inverseArcSegment1 = Segment(self.pt1, self.pt2, abs(self.arc1_bulge))
        self.inverseArcSegment2 = Segment(self.pt7, self.pt8, -self.arc2_bulge)
        self.partialArcSegment = Segment(self.pt1, self.pt10, self.partial_arc_bulge)


    def test_plot(self):
        # Plot the test geometry to help with debug
        # Define Part Geometry
        segment_group = SegmentGroup()
        segment_group.add_segment(self.largeArcSegment)
        segment_group.add_segment(self.lineSegment2)
        segment_group.add_segment(self.lineSegment3)
        segment_group.add_segment(self.arcSegment2)
        groups = []
        groups.append(segment_group)

        for step_over in range(10):
            offset_group = segment_group.offset_path(step_over)
            groups.append(offset_group)

        if 'PIL' in sys.modules:
            plot = Plot()
            plot.backplot(groups)


    def test_get_angle(self):
        angle = self.lineSegment1.get_angle()
        self.assertEqual(angle, math.pi)

        arcAngle = self.arcSegment1.get_angle()
        self.assertEqual(arcAngle, math.radians(abs(self.arc1_angle)))

    def test_angle_from_points(self):

        pt2 = Point(-26.51650, 0.0, -64.01650)
        angle = self.lineSegment1.angle_from_points(self.lineSegment1.start, pt2)
        self.assertAlmostEqual(angle, math.pi, 4)

        # cut the arc down to 90 degrees
        pt1 = Point(-28.70126, 0.0, -5.70904)
        pt2 = Point(-69.29096, 0.0, -103.70126)
        angle = self.arcSegment1.angle_from_points(pt1, pt2)
        self.assertAlmostEqual(angle, -math.pi / 2, 4)

        # cut the arc down to 90 degrees
        pt1 = Point(-128.03301, 0.0, 53.03301)
        pt2 = Point(-181.06601, 0.0, -75.00000)
        angle = self.largeArcSegment.angle_from_points(pt1, pt2)
        self.assertAlmostEqual(angle, -math.pi / 2, 4)

    def test_set_bulge(self):

        tempSegment = self.lineSegment1
        tempSegment.set_bulge(math.radians(self.arc1_angle))
        self.assertEqual(tempSegment.bulge, self.arc1_bulge)

    def test_get_centre_point(self):
        
        lineCentrePt = self.lineSegment1.get_centre_point()
        centrePt = Point(-26.51650, 0.0, -64.01650)
        self.assertAlmostEqual(lineCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(lineCentrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(lineCentrePt.Z, centrePt.Z, 2)

        arcCentrePt = self.arcSegment1.get_centre_point()
        centrePt = Point(0.0, 0.0, -75.0)
        self.assertAlmostEqual(arcCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(arcCentrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(arcCentrePt.Z, centrePt.Z, 2)

        largeArcCentrePt = self.largeArcSegment.get_centre_point()
        centrePt = Point(-90.53301, 0.0, -37.5)
        self.assertAlmostEqual(largeArcCentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(largeArcCentrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(largeArcCentrePt.Z, centrePt.Z, 2)

        invArcCenPt = self.inverseArcSegment1.get_centre_point()
        centrePt = Point(-53.03, 0.0, -53.03)
        self.assertAlmostEqual(invArcCenPt.X, centrePt.X, 2)
        self.assertAlmostEqual(invArcCenPt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(invArcCenPt.Z, centrePt.Z, 2)

        arc2CentrePt = self.arcSegment2.get_centre_point()
        centrePt = Point(-100, 0.0, -200)
        self.assertAlmostEqual(arc2CentrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(arc2CentrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(arc2CentrePt.Z, centrePt.Z, 2)

    def test_get_radius(self):

        lineRadius = self.lineSegment1.get_radius()
        self.assertEqual(lineRadius, 0)

        arcRadius = self.arcSegment1.get_radius()
        self.assertAlmostEqual(arcRadius, 75, 2)

        arcRadius = self.inverseArcSegment1.get_radius()
        self.assertAlmostEqual(arcRadius, 75, 2)

        arcRadius = self.arcSegment2.get_radius()
        self.assertAlmostEqual(arcRadius, 25, 2)

        arcRadius = self.largeArcSegment.get_radius()
        self.assertAlmostEqual(arcRadius, 97.99, 2)

    def test_get_boundbox(self):

        bb = self.lineSegment1.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -53.033, 2)
        self.assertAlmostEqual(bb.z_min, -128.033, 2)
        self.assertAlmostEqual(bb.x_max, 0.0, 2)
        self.assertAlmostEqual(bb.z_max, 0.0, 2)

        bb = self.inverseLineSegment1.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -193.47, 2)
        self.assertAlmostEqual(bb.z_min, -90.533, 2)
        self.assertAlmostEqual(bb.x_max, 37.5, 2)
        self.assertAlmostEqual(bb.z_max, 5.14, 2)

        bb = self.arcSegment1.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -75.0, 2)
        self.assertAlmostEqual(bb.z_min, -128.0299, 2)
        self.assertAlmostEqual(bb.x_max, 0.0, 2)
        self.assertAlmostEqual(bb.z_max, 0.0, 2)

        bb = self.arcSegment2.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -88.3884, 2)
        self.assertAlmostEqual(bb.z_min, -222.14, 2)
        self.assertAlmostEqual(bb.x_max, -75, 2)
        self.assertAlmostEqual(bb.z_max,  -177.86, 2)

        bb = self.inverseArcSegment1.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -53.033, 2)
        self.assertAlmostEqual(bb.z_min, -128.033, 2)
        self.assertAlmostEqual(bb.x_max, 21.967, 2)
        self.assertAlmostEqual(bb.z_max, 0.0, 2)

        bb = self.largeArcSegment.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -188.519, 2)
        self.assertAlmostEqual(bb.z_min,  -135.492, 2)
        self.assertAlmostEqual(bb.x_max, 0.0, 2)
        self.assertAlmostEqual(bb.z_max,  60.4922, 2)

        bb = self.partialArcSegment.get_boundbox()
        self.assertAlmostEqual(bb.x_min, -42.26, 2)
        self.assertAlmostEqual(bb.z_min,  -9.37, 2)
        self.assertAlmostEqual(bb.x_max, 0.0, 2)
        self.assertAlmostEqual(bb.z_max,  0.0, 2)

    def test_get_rotation(self):

        angle = self.lineSegment1.get_rotation()
        self.assertAlmostEqual(angle, 202.5, 2)

    def test_get_length(self):

        length = self.lineSegment1.get_length()
        self.assertAlmostEqual(length, 138.577998, 5)

        arcSegmentLength = self.arcSegment1.get_length()
        self.assertAlmostEqual(arcSegmentLength, 138.577998, 5)

    def test_get_eta(self):
        eta = self.lineSegment1.get_eta()
        self.assertEqual(eta, math.pi / 2)

        arcEta = self.arcSegment1.get_eta()
        self.assertAlmostEqual(arcEta, abs(math.radians(self.arc1_angle / 2)), 5)

    def test_get_epsilon(self):
        epsilon = self.lineSegment1.get_epsilon()
        self.assertEqual(epsilon, 0)

        arcEpsilon = self.arcSegment1.get_epsilon()
        self.assertAlmostEqual(arcEpsilon, abs(math.radians(self.arc1_angle / 4)), 5)

    def test_get_phi(self):
        phi = self.lineSegment1.get_phi()
        self.assertEqual(phi, 0)

        arcPhi = self.arcSegment1.get_phi()
        self.assertAlmostEqual(arcPhi, 0.98175, 5)

    def test_is_same(self):
        lineComparison = self.lineSegment1.is_same(self.lineSegment1)
        self.assertTrue(lineComparison)

        arcComparison = self.arcSegment1.is_same(self.arcSegment1)
        self.assertTrue(arcComparison)

        lineArcComparison = self.lineSegment1.is_same(self.arcSegment1)
        self.assertFalse(lineArcComparison)


    def test_offset(self):

        #TODO: Offset Line Test

        offset_centrePt = self.arcSegment1.offset(5).get_centre_point()
        centrePt = Point(0.0, 0.0, -75.0)
        self.assertAlmostEqual(offset_centrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(offset_centrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(offset_centrePt.Z, centrePt.Z, 2)

        offset_centrePt = self.largeArcSegment.offset(5).get_centre_point()
        centrePt = Point(-90.533, 0.0, -37.5)
        self.assertAlmostEqual(offset_centrePt.X, centrePt.X, 2)
        self.assertAlmostEqual(offset_centrePt.Y, centrePt.Y, 2)
        self.assertAlmostEqual(offset_centrePt.Z, centrePt.Z, 2)


    def test_intersect(self):

        # intersection1
        intersect, pts = self.lineSegment1.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        self.assertAlmostEqual(pt.X, -26.514777, 3)
        self.assertAlmostEqual(pt.Z, -64.014462, 3)

        # intersection2
        intersect, pts = self.arcSegment1.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        self.assertAlmostEqual(pt.X, -69.288457, 3)
        self.assertAlmostEqual(pt.Z, -46.297345, 3)

        # intersection3
        intersect, pts = self.inverseArcSegment1.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        self.assertAlmostEqual(pt.X, 16.258457, 3)
        self.assertAlmostEqual(pt.Z, -81.731757, 3)

        # intersection4
        intersect, pts = self.largeArcSegment.intersect(self.inverseLineSegment1)
        pt = pts[0]
        self.assertTrue(intersect)
        self.assertAlmostEqual(pt.X, -181.06012, 3)
        self.assertAlmostEqual(pt.Z, -0.0002915, 3)

        # false intersection tests
        intersect, pts = self.inverseArcSegment2.intersect(self.lineSegment1)
        self.assertFalse(intersect)

        intersect, pts = self.arcSegment2.intersect(self.lineSegment3)
        self.assertFalse(intersect)


if __name__ == '__main__':
    unittest.main()
