import math
import unittest

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class test_InsideCrossings(unittest.TestCase):
    def polygon(self, points):
        group = SegmentGroup()
        for start, end in zip(points, points[1:]):
            group.addSegment(Segment(Point(*start), Point(*end)))
        return group

    def test_empty_geometry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            SegmentGroup().isInside(Point(0, 0))

    def test_shared_vertex_does_not_flip_sign(self):
        points = [(0, 0), (3, -1), (6, -3), (6, -6), (0, -6)]
        for vertices in (points, list(reversed(points))):
            group = self.polygon(vertices)
            for x in (2.9999, 3, 3.0001):
                with self.subTest(vertices=vertices, x=x):
                    self.assertTrue(group.isInside(Point(x, -4)))
                    self.assertAlmostEqual(group.sdv(Point(x, -4)), -2, places=4)
                    self.assertFalse(group.isInside(Point(x, 1)))
                    self.assertFalse(group.isInside(Point(x, -7)))

    def test_vertex_extrema_collinear_runs_and_boundaries(self):
        group = self.polygon([(0, 0), (3, 0), (3, -1), (6, -1),
                              (6, -6), (3, -6), (3, -5), (0, -5)])
        for x in (2.9999, 3, 3.0001):
            with self.subTest(x=x):
                self.assertTrue(group.isInside(Point(x, -3)))
                self.assertFalse(group.isInside(Point(x, 1)))
                self.assertFalse(group.isInside(Point(x, -7)))
        for point in ((3, -0.5), (4, -1), (6, -3), (0, -3)):
            with self.subTest(boundary=point):
                self.assertTrue(group.isInside(Point(*point)))
        for x in (2.9999, 3, 3.0001):
            self.assertEqual(group.isInside(Point(x, -0.5)), x <= 3)

    def test_axis_fillers_are_preserved(self):
        group = self.polygon([(2, 0), (2, -4)])
        self.assertTrue(group.isInside(Point(1, -2)))
        self.assertTrue(group.isInside(Point(0, -2)))
        self.assertFalse(group.isInside(Point(-1, -2)))
        self.assertFalse(group.isInside(Point(1, 1)))
        self.assertFalse(group.isInside(Point(1, -5)))

    def test_arc_crossings_shared_endpoints_and_tangencies(self):
        for direction in (1, -1):
            circle = SegmentGroup()
            circle.addSegment(Segment(Point(0, 0), Point(2, 0), direction))
            circle.addSegment(Segment(Point(2, 0), Point(0, 0), direction))
            for x in (0, 0.0001, 0.9999, 1, 1.0001, 1.9999, 2, 2.0001):
                for z in (-1.2, -0.5, 0.5, 1.2):
                    with self.subTest(direction=direction, x=x, z=z):
                        self.assertEqual(circle.isInside(Point(x, z)),
                                         (x - 1) ** 2 + z ** 2 < 1)
            for point in ((0, 0), (2, 0), (1, 1), (1, -1), (1, 0)):
                self.assertTrue(circle.isInside(Point(*point)))

    def test_arc_line_shared_vertex(self):
        for reverse in (False, True):
            group = SegmentGroup()
            if reverse:
                group.addSegment(Segment(Point(0, -2), Point(2, 0)))
                group.addSegment(Segment(Point(2, 0), Point(0, 0), -1))
            else:
                group.addSegment(Segment(Point(0, 0), Point(2, 0), 1))
                group.addSegment(Segment(Point(2, 0), Point(0, -2)))
            for x in (1.9999, 2, 2.0001):
                with self.subTest(reverse=reverse, x=x):
                    self.assertEqual(group.isInside(Point(x, 0)), x <= 2)
                    self.assertFalse(group.isInside(Point(x, -3)))

    def test_major_arc_counts_both_branches(self):
        for reverse in (False, True):
            group = SegmentGroup()
            start, end, bulge = (Point(0, 0), Point(2, 0), math.tan(3 * math.pi / 8))
            if reverse:
                start, end, bulge = end, start, -bulge
            group.addSegment(Segment(start, end, bulge))
            group.addSegment(Segment(end, start))
            for x in (-0.5, -0.2, 0, 0.5, 1, 1.5, 2, 2.2, 2.5):
                for z in (-0.5, 0.5, 1, 2, 2.5):
                    with self.subTest(reverse=reverse, x=x, z=z):
                        self.assertEqual(group.isInside(Point(x, z)),
                                         z >= 0 and (x - 1) ** 2 + (z - 1) ** 2 <= 2)
