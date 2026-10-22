import math
import random
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class TestDefeatureBounds(unittest.TestCase):
    @staticmethod
    def group(segments):
        group = SegmentGroup()
        for segment in segments:
            group.addSegment(segment)
        return group

    @classmethod
    def profile(cls, vertices):
        points = [Point(*vertex) for vertex in vertices]
        return cls.group([Segment(start, end)
                          for start, end in zip(points, points[1:])])

    @staticmethod
    def coordinates(group):
        return [(s.start.X, s.start.Z, s.end.X, s.end.Z, s.bulge)
                for s in group.getSegments()]

    def test_group_intersections_match_unfiltered_narrow_phase(self):
        rng = random.Random(1301)
        bulges = (0, 0, -math.tan(math.pi / 8), math.tan(math.pi / 8),
                  -1, 1, -math.tan(3 * math.pi / 8), math.tan(3 * math.pi / 8))
        for index in range(1200):
            scale = (0.01, 1, 100, 10000)[index % 4]
            origin = rng.choice((0, 1000, -1000))
            segments = [
                Segment(Point(origin + rng.uniform(-2, 2) * scale,
                              origin + rng.uniform(-2, 2) * scale),
                        Point(origin + rng.uniform(-2, 2) * scale,
                              origin + rng.uniform(-2, 2) * scale),
                        rng.choice(bulges))
                for _ in range(4)
            ]
            part, tool = segments[:2], segments[2:]
            expected = any(edge.intersect(target, False)
                           for edge in tool for target in part)
            with self.subTest(index=index, scale=scale):
                self.assertEqual(self.group(part).intersectsGroup(self.group(tool)),
                                 expected)

    def test_arc_extrema_beyond_endpoints_are_not_pruned(self):
        for bulge in (-math.tan(math.pi / 8), math.tan(math.pi / 8),
                      -1, 1, -math.tan(3 * math.pi / 8), math.tan(3 * math.pi / 8)):
            arc = Segment(Point(1, 0), Point(0, 1), bulge)
            centre, radius = arc.getCentrePoint(), arc.getRadius()
            angle = math.atan2(arc.start.Z - centre.Z, arc.start.X - centre.X)
            for fraction in (0.37, 0.61):
                z = centre.Z + radius * math.sin(angle - 4 * math.atan(bulge) * fraction)
                line = Segment(Point(centre.X - 2 * radius, z),
                               Point(centre.X + 2 * radius, z))
                with self.subTest(bulge=bulge, fraction=fraction):
                    self.assertTrue(line.intersect(arc, False))
                    self.assertTrue(self.group([arc]).intersectsGroup(self.group([line])))

    def test_contacts_degenerate_edges_and_empty_groups(self):
        segments = [
            Segment(Point(0, 0), Point(1, 0)),
            Segment(Point(1, 0), Point(1, 1)),
            Segment(Point(0, 0), Point(0, 0)),
            Segment(Point(0, 0), Point(1, 0), 1),
            Segment(Point(0, 0), Point(1, 0), -1),
        ]
        for first in segments:
            for second in segments:
                expected = bool(second.intersect(first, False))
                self.assertEqual(self.group([first]).intersectsGroup(self.group([second])),
                                 expected)
        self.assertFalse(self.group([]).intersectsGroup(self.group(segments)))
        self.assertFalse(self.group(segments).intersectsGroup(self.group([])))

    def test_rounded_arc_contact_outside_geometric_bounds_is_retained(self):
        arc = Segment(Point(100.1, 0), Point(100, 0.1), -math.tan(math.pi / 8))
        bounds, centre = arc.Boundbox(), arc.getCentrePoint()
        line = Segment(Point(bounds.XMax + 0.0015, centre.Z - 0.2),
                       Point(bounds.XMax + 0.0015, centre.Z + 0.2))
        # Legacy radial rounding accepts this contact beyond the geometric bounds.
        self.assertGreater(line.start.X - bounds.XMax, 0.001)
        self.assertTrue(line.intersect(arc, False))
        self.assertTrue(self.group([arc]).intersectsGroup(self.group([line])))

    def test_intersection_preparation_is_refreshed_after_edits(self):
        part = self.profile([(10, 0), (10, -10)])
        tool = self.profile([(0, -5), (2, -5)])
        self.assertFalse(part.intersectsGroup(tool))
        part.addSegment(Segment(Point(1, 0), Point(1, -10)))
        self.assertTrue(part.intersectsGroup(tool))

    def groove(self):
        return self.profile([(0, 0), (10, 0), (10, -5), (6, -5),
                             (6, -11), (10, -11), (10, -18), (0, -18)])

    def test_defeature_retains_legacy_contours_and_inputs(self):
        source = self.groove()
        tool = self.profile([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
        stock = BoundBox(Point(0, 1), Point(12, -20))
        original_source, original_tool = self.coordinates(source), self.coordinates(tool)
        # Captured from the unfiltered implementation, including float accumulation.
        common = [(0.0, 0.009999999776482582), (10.005000114440918, 0.0)]
        for grooving in (False, True):
            expected = common + ([
                (10.005000114440918, -4.99001932144165),
                (6.005000114440918, -7.000065326690674),
                (6.005000114440918, -10.990156173706055),
                (10.005000114440918, -11.00015640258789),
            ] if grooving else []) + [(10.005000114440918, -17.99031639099121)]
            with self.subTest(grooving=grooving):
                result = source.defeature(stock, tool, grooving)
                expected_segments = [(a[0], a[1], b[0], b[1], 0)
                                     for a, b in zip(expected, expected[1:])]
                self.assertEqual(self.coordinates(result), expected_segments)
                self.assertEqual(self.coordinates(source), original_source)
                self.assertEqual(self.coordinates(tool), original_tool)

    def test_translated_tool_retains_legacy_chord_footprint(self):
        source = self.groove()
        linear = self.profile([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
        curved = self.group([Segment(edge.start, edge.end, 0.5 if i == 0 else 0)
                             for i, edge in enumerate(linear.getSegments())])
        stock = BoundBox(Point(0, 1), Point(12, -20))
        for grooving in (False, True):
            self.assertEqual(self.coordinates(source.defeature(stock, curved, grooving)),
                             self.coordinates(source.defeature(stock, linear, grooving)))


if __name__ == '__main__':
    unittest.main()
