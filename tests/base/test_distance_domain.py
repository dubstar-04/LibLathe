import math
import unittest

from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class test_DistanceDomain(unittest.TestCase):
    def profile(self, points):
        group = SegmentGroup()
        for start, end in zip(points, points[1:]):
            group.addSegment(Segment(Point(*start), Point(*end)))
        return group

    def tree(self, group, offset):
        tree = Quadtree()
        tree.initialise(group, Point(16, -4), 32, 32)
        points = tree.getOffset(offset)
        return tree, points

    def test_closure_distances_are_continuous(self):
        vertices = [(10, 0), (10, -10)]
        for points in (vertices, list(reversed(vertices))):
            group = self.profile(points)
            for epsilon in (0.1, 0.001, 0.0001):
                for outside, inside in (
                    (Point(5, epsilon), Point(5, -epsilon)),
                    (Point(5, -10 - epsilon), Point(5, -10 + epsilon)),
                    (Point(-epsilon, -5), Point(epsilon, -5)),
                ):
                    with self.subTest(points=points, epsilon=epsilon,
                                      outside=(outside.X, outside.Z)):
                        self.assertAlmostEqual(group.sdv(outside), epsilon,
                                               delta=1e-6)
                        self.assertAlmostEqual(group.sdv(inside), -epsilon,
                                               delta=1e-6)
                        self.assertLessEqual(
                            abs(group.sdv(outside) - group.sdv(inside)),
                            outside.distanceTo(inside) + 1e-6)
            for boundary in ((5, 0), (5, -10), (0, -5), (10, -5)):
                self.assertEqual(group.sdv(Point(*boundary)), 0)

    def test_overlapping_closures_do_not_add_axis_spurs(self):
        closed = self.profile([(2, 0), (4, 0), (3, 2), (2, 0)])
        semicircle = SegmentGroup()
        semicircle.addSegment(Segment(Point(2, 0), Point(4, 0), 1))
        for group in (closed, semicircle):
            for x in (0, 0.5, 1):
                with self.subTest(group=group, x=x):
                    self.assertFalse(group.isInside(Point(x, 0)))
                    self.assertAlmostEqual(group.sdv(Point(x, 0)), 2 - x)

    def test_implicit_closures_do_not_generate_caps(self):
        group = self.profile([(10, 0), (10, -10)])
        for offset in (1, -1):
            _, points = self.tree(group, offset)
            with self.subTest(offset=offset):
                self.assertGreater(len(points), 10)
                for point in points:
                    if offset > 0:
                        self.assertGreaterEqual(point.X, 10 - 1e-5)
                    else:
                        self.assertAlmostEqual(point.X, 9, delta=1e-5)
                        self.assertLessEqual(point.Z, -1 + 1e-5)
                        self.assertGreaterEqual(point.Z, -9 - 1e-5)

    def test_explicit_faces_remain_in_output(self):
        group = self.profile([(0, 0), (10, 0), (10, -10), (0, -10)])
        _, points = self.tree(group, 1)
        self.assertTrue(any(1 < p.X < 9 and abs(p.Z + 11) < 1e-5
                            for p in points))

    def rectangle_distance(self, x, z):
        qx, qz = abs(x - 5) - 5, abs(z + 5) - 5
        return (math.hypot(max(qx, 0), max(qz, 0)) +
                min(max(qx, qz), 0))

    def quarter_disk_distance(self, x, z):
        dz = z + 8
        radius_distance = math.hypot(x, dz)
        if x >= 0 and dz >= 0:
            arc = abs(radius_distance - 8)
        else:
            arc = min(math.hypot(x, dz - 8), math.hypot(x - 8, dz))
        axis = math.hypot(x, dz - min(8, max(0, dz)))
        end = math.hypot(x - min(8, max(0, x)), dz)
        distance = min(arc, axis, end)
        inside = x >= 0 and dz >= 0 and radius_distance <= 8
        return -distance if inside else distance

    def test_signed_distances_match_closed_line_and_arc_regions(self):
        rectangle = self.profile([(10, 0), (10, -10)])
        arc = SegmentGroup()
        arc.addSegment(Segment(Point(0, 0), Point(8, -8),
                               math.tan(math.pi / 8)))
        for group, expected in (
            (rectangle, self.rectangle_distance),
            (arc, self.quarter_disk_distance),
        ):
            for ix in range(-4, 25):
                for iz in range(-24, 5):
                    x, z = ix / 2, iz / 2
                    with self.subTest(shape=expected.__name__, x=x, z=z):
                        self.assertAlmostEqual(group.sdv(Point(x, z)),
                                               expected(x, z), delta=2e-5)

    def test_pruning_keeps_cells_crossed_by_closed_boundary_contours(self):
        rectangle = self.profile([(10, 0), (10, -10)])
        arc = SegmentGroup()
        arc.addSegment(Segment(Point(0, 0), Point(8, -8),
                               math.tan(math.pi / 8)))
        for group, expected in (
            (rectangle, self.rectangle_distance),
            (arc, self.quarter_disk_distance),
        ):
            for offset in (-1, 0, 1):
                tree, _ = self.tree(group, offset)
                nodes = tree.getNodes()
                keys = {(n.center.X, n.center.Z, n.width) for n in nodes}
                checked = 0
                for node in nodes:
                    if node.width <= 0.2:
                        continue
                    child = (node.center.X - node.width / 4,
                             node.center.Z + node.width / 4, node.width / 2)
                    if child in keys:
                        continue
                    values = [
                        expected(node.center.X + node.width * (i / 8 - 0.5),
                                 node.center.Z + node.width * (j / 8 - 0.5))
                        for i in range(9) for j in range(9)
                    ]
                    with self.subTest(shape=expected.__name__, offset=offset,
                                      center=(node.center.X, node.center.Z),
                                      width=node.width):
                        self.assertFalse(min(values) + 1e-6 < offset <
                                         max(values) - 1e-6,
                                         'Pruned cell contains a contour crossing')
                    checked += 1
                self.assertGreater(checked, 0)

    def test_empty_distance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            SegmentGroup().sdv(Point(1, 0))

    def test_nonfinite_queries_are_rejected(self):
        group = self.profile([(10, 0), (10, -10)])
        for value in (float('inf'), -float('inf'), float('nan')):
            for query in (Point(value, 0), Point(1, value)):
                with self.subTest(value=value, query=(query.X, query.Z)):
                    with self.assertRaisesRegex(ValueError, 'finite'):
                        group.sdv(query)
