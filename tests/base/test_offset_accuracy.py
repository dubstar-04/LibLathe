import math
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.tool.tool import Tool


class test_OffsetAccuracy(unittest.TestCase):
    contour_tolerance = 0.05
    sample_spacing = 0.01

    def polygon(self, vertices):
        group = SegmentGroup()
        for start, end in zip(vertices, vertices[1:]):
            group.addSegment(Segment(Point(*start), Point(*end)))
        return group

    def points(self, group, offset):
        bounds = group.boundbox()
        padding = abs(offset) + 0.2
        xmin = min(0, bounds.XMin)
        size = max(bounds.XMax + padding - xmin,
                   bounds.ZLength() + 2 * padding)
        tree = Quadtree()
        tree.initialise(group, Point(xmin + size / 2,
                                    bounds.ZMin - padding + size / 2),
                        size, size)
        return tree.getOffset(offset)

    def contour_error_bound(self, points, distance, offset):
        self.assertGreater(len(points), 1)
        worst = 0
        for start, end in zip(points, points[1:]):
            intervals = max(1, math.ceil(start.distanceTo(end) /
                                         self.sample_spacing))
            residual = max(
                abs(distance(start.lerp(end, i / intervals)) - offset)
                for i in range(intervals + 1)
            )
            # A signed distance is 1-Lipschitz between adjacent samples.
            worst = max(worst, residual +
                        start.distanceTo(end) / (2 * intervals))
        return worst

    def assert_contours_accurate(self, group, offset, distance=None):
        distance = group.sdv if distance is None else distance
        raw = self.points(group, offset)
        segments = group.offset(offset).getSegments()
        self.assertGreater(len(segments), 0)
        for previous, following in zip(segments, segments[1:]):
            self.assertTrue(previous.end.isSame(following.start))
        simplified = [segments[0].start] + [s.end for s in segments]
        for stage, points in (('raw', raw), ('simplified', simplified)):
            with self.subTest(stage=stage):
                self.assertTrue(all(math.isfinite(p.X) and math.isfinite(p.Z)
                                    for p in points))
                self.assertLessEqual(
                    self.contour_error_bound(points, distance, offset),
                    self.contour_tolerance)
        return raw, simplified

    def assert_covered(self, expected, points):
        segments = [Segment(a, b) for a, b in zip(points, points[1:])]
        self.assertGreater(len(expected), 0)
        worst = max(min(s.distanceToPoint(p) for s in segments)
                    for p in expected)
        self.assertLessEqual(worst, self.contour_tolerance)

    def test_rectangle_contours_match_analytic_distance(self):
        group = self.polygon([(0, 0), (20, 0), (20, -10), (0, -10)])

        def distance(p):
            x, z = abs(p.X - 10) - 10, abs(p.Z + 5) - 5
            return math.hypot(max(x, 0), max(z, 0)) + min(max(x, z), 0)

        for offset in (-0.1, 0, 0.2, 1):
            with self.subTest(offset=offset):
                raw, simplified = self.assert_contours_accurate(
                    group, offset, distance)
                expected = [Point(20 + offset, -0.1 - i * 0.01)
                            for i in range(981)]
                expected += [Point(0.1 + i * 0.01, -10 - offset)
                             for i in range(1981)]
                for points in (raw, simplified):
                    self.assert_covered(expected, points)

    def test_grooves_corners_and_feature_switch_contours(self):
        for width in (2, 0.3):
            group = self.polygon([
                (0, 0), (8, 0), (8, -2), (4, -2),
                (4, -2 - width), (8, -2 - width), (8, -8), (0, -8)])
            for offset in (-0.1, 0, 0.1, 1):
                with self.subTest(width=width, offset=offset):
                    if width == 2 and offset == 1:
                        with self.assertRaisesRegex(RuntimeError, 'Offset contour'):
                            group.offset(offset)
                        with self.assertRaisesRegex(RuntimeError, 'Offset contour'):
                            self.points(group, offset)
                        continue
                    raw, simplified = self.assert_contours_accurate(group, offset)
                    if offset == 0:
                        expected = []
                        for segment in group.getSegments():
                            intervals = max(1, math.ceil(
                                segment.start.distanceTo(segment.end) /
                                self.sample_spacing))
                            expected.extend(segment.start.lerp(segment.end, i / intervals)
                                            for i in range(intervals + 1))
                        for points in (raw, simplified):
                            self.assert_covered(expected, points)

    def test_small_loops_match_analytic_circle(self):
        for radius in (0.35, 0.08):
            group = SegmentGroup()
            top, bottom = Point(2, -2 + radius), Point(2, -2 - radius)
            group.addSegment(Segment(top, bottom, 1))
            group.addSegment(Segment(bottom, top, 1))

            def distance(p):
                return math.hypot(p.X - 2, p.Z + 2) - radius

            for offset in (-radius / 4, 0, 0.1):
                with self.subTest(radius=radius, offset=offset):
                    raw, simplified = self.assert_contours_accurate(
                        group, offset, distance)
                    expected = [
                        Point(2 + (radius + offset) * math.cos(i * math.tau / 720),
                              -2 + (radius + offset) * math.sin(i * math.tau / 720))
                        for i in range(720)
                    ]
                    expected = [p for p in expected if p.Z <= top.Z]
                    for points in (raw, simplified):
                        self.assert_covered(expected, points)

    def test_quarter_disk_contours_match_analytic_distance(self):
        group = SegmentGroup()
        group.addSegment(Segment(Point(0, 0), Point(8, -8),
                                 math.tan(math.pi / 8)))

        def distance(point):
            x, z = point.X, point.Z + 8
            radius = math.hypot(x, z)
            arc = (abs(radius - 8) if x >= 0 and z >= 0 else
                   min(math.hypot(x, z - 8), math.hypot(x - 8, z)))
            axis = math.hypot(x, z - min(8, max(0, z)))
            end = math.hypot(x - min(8, max(0, x)), z)
            value = min(arc, axis, end)
            return -value if x >= 0 and z >= 0 and radius <= 8 else value

        for offset in (-0.1, 0, 1, 4):
            with self.subTest(offset=offset):
                raw, simplified = self.assert_contours_accurate(
                    group, offset, distance)
                expected = [
                    Point((8 + offset) * math.sin(i * math.pi / 2000),
                          -8 + (8 + offset) * math.cos(i * math.pi / 2000))
                    for i in range(1001)
                ]
                expected = [p for p in expected
                            if p.Z <= 0 and abs(distance(p) - offset) < 1e-5]
                for points in (raw, simplified):
                    self.assert_covered(expected, points)

    def test_tree_recovers_after_collapsed_contour_error(self):
        group = self.polygon([
            (0, 0), (8, 0), (8, -2), (4, -2),
            (4, -4), (8, -4), (8, -8), (0, -8)])
        tree = Quadtree()
        tree.initialise(group, Point(5.2, -4), 10.4, 10.4)
        for _ in range(2):
            with self.assertRaisesRegex(RuntimeError, 'Offset contour'):
                tree.getOffset(1)
            actual = [(p.X, p.Z) for p in tree.getOffset(0)]
            fresh = Quadtree()
            fresh.initialise(group, Point(5.2, -4), 10.4, 10.4)
            self.assertEqual(actual, [(p.X, p.Z) for p in fresh.getOffset(0)])

    def test_supported_inserts_defeature_the_illustrated_narrow_groove(self):
        group = self.polygon([
            (0, 0), (8, 0), (8, -2), (4, -2),
            (4, -4), (8, -4), (8, -8), (0, -8)])
        stock = BoundBox(Point(0, -9), Point(10, 1))
        for code, rotation in (
            ('DCMT070204R', 0), ('DCMT070204R', 22.5),
            ('DCMT070204R', 45), ('TCMT160404N', 0),
        ):
            tool = Tool(code)
            if rotation:
                tool.set_rotation(rotation)
            for grooving in (False, True):
                with self.subTest(tool=code, rotation=rotation, grooving=grooving):
                    source = group.defeature(stock, tool.get_segmentgroup(), grooving)
                    wall = [s for s in source.getSegments()
                            if s.start.Z > -3 > s.end.Z]
                    self.assertEqual(len(wall), 1)
                    self.assertAlmostEqual(wall[0].start.X, 8, delta=0.01)
                    self.assertAlmostEqual(wall[0].end.X, 8, delta=0.01)
                    for offset in (-0.1, 0, 0.5, 1, 2):
                        with self.subTest(offset=offset):
                            self.assert_contours_accurate(source, offset)

    def test_accessible_grooves_with_supported_diamond_insert(self):
        for width in (6, 10):
            end = -width - 6
            group = self.polygon([
                (0, 0), (8, 0), (8, -2), (4, -2),
                (4, -2 - width), (8, -2 - width), (8, end), (0, end)])
            stock = BoundBox(Point(0, end - 1), Point(10, 1))
            for rotation in (0, 22.5):
                tool = Tool('DCMT070204R')
                if rotation:
                    tool.set_rotation(rotation)
                for grooving in (False, True):
                    with self.subTest(width=width, rotation=rotation,
                                      grooving=grooving):
                        source = group.defeature(stock, tool.get_segmentgroup(),
                                                 grooving)
                        groove = [
                            s.start.lerp(s.end, i / 100)
                            for s in source.getSegments() for i in range(101)
                            if -2 - width < s.start.lerp(s.end, i / 100).Z < -2
                        ]
                        self.assertGreater(len(groove), 0)
                        expected = 4 if grooving else 8
                        self.assertAlmostEqual(min(p.X for p in groove),
                                               expected, delta=0.01)
                        for offset in (-0.1, 0, 0.5, 1, 2, width / 2):
                            with self.subTest(offset=offset):
                                self.assert_contours_accurate(source, offset)

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
                    if index == 1 and offset == 1:
                        with self.assertRaisesRegex(RuntimeError, 'Offset contour'):
                            self.points(group, offset)
                        continue
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
