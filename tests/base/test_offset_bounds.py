import math
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class test_OffsetBounds(unittest.TestCase):
    def rectangle(self, radius, length, x=0, z=0):
        group = SegmentGroup()
        points = [Point(x, z), Point(x + radius, z),
                  Point(x + radius, z - length), Point(x, z - length)]
        for start, end in zip(points, points[1:]):
            group.addSegment(Segment(start, end))
        return group

    def padded_points(self, group, offset):
        bounds = group.boundbox()
        padding = abs(offset) + 2
        xmin = min(0, bounds.XMin)
        zmin = bounds.ZMin - padding
        size = max(bounds.XMax + padding - xmin, bounds.ZLength() + 2 * padding)
        tree = Quadtree()
        tree.initialise(group, Point(xmin + size / 2, zmin + size / 2), size, size)
        return tree.getOffset(offset)

    def padded_offset(self, group, offset):
        points = self.padded_points(group, offset)
        return SegmentGroup().fromPoints(SegmentGroup().reduce(points, 0.01))

    def test_rectangular_offsets_include_side_and_bottom(self):
        for radius, length, offset, x, z in (
            (20, 10, 5, 0, 0),
            (2, 20, 1, 0, 0),
            (20, 10, 8, 0, 0),
            (20, 10, 5, 10, 7),
            (20, 10, 5, 0, -30),
            (20, 10, 0, 0, 0),
            (20, 10, -0.1, 0, 0),
        ):
            with self.subTest(radius=radius, length=length, offset=offset, x=x, z=z):
                group = self.rectangle(radius, length, x, z)
                result = group.offset(offset)
                bounds = result.boundbox()
                self.assertAlmostEqual(bounds.XMax, x + radius + offset, places=4)
                self.assertAlmostEqual(bounds.ZMin, z - length - offset, places=4)
                self.assertLessEqual(bounds.ZMax, z)
                self.assertGreaterEqual(bounds.XMin, 0)
                reference = self.padded_offset(group, offset).boundbox()
                self.assertAlmostEqual(bounds.XMax, reference.XMax, places=4)
                self.assertAlmostEqual(bounds.ZMin, reference.ZMin, places=4)

    def test_curved_profile_reaches_analytic_extents_within_simplification_budget(self):
        group = SegmentGroup()
        group.addSegment(Segment(Point(0, 0), Point(10, -10), 0.25))
        group.addSegment(Segment(Point(10, -10), Point(10, -20)))
        group.addSegment(Segment(Point(10, -20), Point(0, -20)))
        for offset in (1, 5):
            with self.subTest(offset=offset):
                result = group.offset(offset)
                reference = self.padded_points(group, offset)
                self.assertGreater(result.count(), 0)
                bounds = result.boundbox()
                self.assertAlmostEqual(max(p.X for p in reference), 10 + offset, places=4)
                self.assertAlmostEqual(min(p.Z for p in reference), -20 - offset, places=4)
                # RDP may move an extremum by its existing 0.01 distance tolerance.
                self.assertLessEqual(abs(bounds.XMax - (10 + offset)), 0.01)
                self.assertLessEqual(abs(bounds.ZMin - (-20 - offset)), 0.01)
                for segment in result.getSegments():
                    for point in (segment.start, segment.end):
                        self.assertTrue(math.isfinite(point.X) and math.isfinite(point.Z))
                        self.assertGreaterEqual(point.X, 0)
                        self.assertLessEqual(point.Z, 0)

    def test_curved_chords_and_rdp_have_separate_budgets(self):
        rectangle = self.rectangle(20, 10)
        curve = SegmentGroup()
        curve.addSegment(Segment(Point(0, 0), Point(10, -10), 0.25))
        curve.addSegment(Segment(Point(10, -10), Point(10, -20)))
        curve.addSegment(Segment(Point(10, -20), Point(0, -20)))

        def worst_error(group, points, offset):
            return max(
                abs(group.sdv(start.lerp(end, i / 8)) - offset)
                for start, end in zip(points, points[1:])
                for i in range(9)
            )

        for index, group in enumerate((rectangle, curve)):
            for offset in (1, 5):
                with self.subTest(shape=index, offset=offset):
                    raw = self.padded_points(group, offset)
                    raw_error = worst_error(group, raw, offset)
                    result = group.offset(offset).getSegments()
                    simplified = [result[0].start] + [s.end for s in result]
                    simplified_error = worst_error(group, simplified, offset)
                    self.assertLessEqual(raw_error, 0.01)
                    self.assertLessEqual(simplified_error, 0.02)
                    self.assertLessEqual(simplified_error,
                                         raw_error + 0.01 + 1e-4)
