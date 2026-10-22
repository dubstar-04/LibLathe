import math
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class test_OffsetAccuracy(unittest.TestCase):
    def polygon(self, vertices):
        group = SegmentGroup()
        for start, end in zip(vertices, vertices[1:]):
            group.addSegment(Segment(Point(*start), Point(*end)))
        return group

    def points(self, group, offset):
        bounds = group.boundbox()
        padding = abs(offset) + 0.2
        size = max(bounds.XMax + padding, bounds.ZLength() + 2 * padding)
        tree = Quadtree()
        tree.initialise(group, Point(size / 2, bounds.ZMin - padding + size / 2),
                        size, size)
        return tree.getOffset(offset)

    def test_zero_offsets_keep_all_profile_sides(self):
        group = self.polygon([(0, 0), (20, 0), (20, -10), (0, -10)])
        for offset in (0.0, -0.0):
            with self.subTest(offset=offset):
                points = self.points(group, offset)
                self.assertGreater(len(points), 10)
                self.assertAlmostEqual(max(p.X for p in points), 20, places=5)
                self.assertAlmostEqual(min(p.Z for p in points), -10, places=5)
                self.assertTrue(any(p.Z == 0 for p in points))
                for point in points:
                    self.assertAlmostEqual(group.sdv(point), 0, delta=1e-5)

    def test_projected_candidates_remain_on_the_requested_level(self):
        shapes = [
            self.polygon([(0, 0), (20, 0), (20, -10), (0, -10)]),
            self.polygon([(0, 0), (8, 0), (8, -2), (4, -2),
                          (4, -4), (8, -4), (8, -8), (0, -8)]),
        ]
        arc = SegmentGroup()
        arc.addSegment(Segment(Point(0, 0), Point(8, -8),
                               math.tan(math.pi / 8)))
        shapes.append(arc)
        for index, group in enumerate(shapes):
            for offset in (-0.1, 0, 1, 4):
                with self.subTest(shape=index, offset=offset):
                    points = self.points(group, offset)
                    self.assertGreater(len(points), 1)
                    self.assertLessEqual(
                        max(abs(group.sdv(p) - offset) for p in points), 1e-4)

    def test_inward_rectangle_keeps_corner_intersections(self):
        group = self.polygon([(0, 0), (20, 0), (20, -10), (0, -10)])
        points = self.points(group, -0.1)
        for corner in (Point(19.9, -0.1), Point(19.9, -9.9)):
            self.assertLessEqual(min(p.distanceTo(corner) for p in points), 1e-5)
        result = group.offset(-0.1)
        for segment in result.getSegments():
            for i in range(9):
                point = segment.start.lerp(segment.end, i / 8)
                self.assertAlmostEqual(group.sdv(point), -0.1, delta=1e-4)
