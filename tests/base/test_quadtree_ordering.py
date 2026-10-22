import json
from pathlib import Path
import unittest

from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class TestQuadtreeOrdering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'data' / 'quadtree_ordering.json'
        cls.cases = json.loads(path.read_text())['cases']

    @staticmethod
    def extract(case):
        group = SegmentGroup()
        for x, z, xx, zz, bulge in case['segments']:
            group.addSegment(Segment(Point(x, z), Point(xx, zz), bulge))
        x, z, size = case['root']
        tree = Quadtree()
        tree.initialise(group, Point(x, z), size, size)
        return group, tree.getOffset(case['offset'])

    @staticmethod
    def greedy_reference(datum, points):
        remaining = sorted(points, key=lambda point: (point.X, point.Z))
        target = min(remaining, key=lambda point: (-point.Z, datum.distanceTo(point)))
        result = []
        while remaining:
            # The native float distance and canonical index define rounded ties.
            index = min(range(len(remaining)),
                        key=lambda i: target.distanceTo(remaining[i]))
            target = remaining.pop(index)
            result.append([target.X, target.Z])
        return result

    def assert_contour_close(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for row, (actual_values, expected_values) in enumerate(zip(actual, expected)):
            self.assertEqual(len(actual_values), len(expected_values))
            for component, (value, reference) in enumerate(
                    zip(actual_values, expected_values)):
                # Float32 snapshots can differ in the last bits across builds.
                self.assertAlmostEqual(
                    value, reference, delta=max(1e-7, abs(reference) * 2e-7),
                    msg=f'Row {row}, component {component}')

    def test_ordering_matches_pre_index_contours(self):
        for case in self.cases:
            with self.subTest(profile=case['name'], offset=case['offset']):
                group, points = self.extract(case)
                actual = [[point.X, point.Z] for point in points]
                self.assert_contour_close(actual, case['expected_points'])
                self.assertEqual(len(actual), len({tuple(point) for point in actual}))
                if case['expected_segments'] is not None:
                    result = group.offset(case['offset'])
                    self.assert_contour_close(
                        [[s.start.X, s.start.Z, s.end.X, s.end.Z, s.bulge]
                         for s in result.getSegments()],
                        case['expected_segments'])

    def test_every_greedy_choice_matches_float_distance_reference(self):
        for case in self.cases:
            with self.subTest(profile=case['name'], offset=case['offset']):
                _, points = self.extract(case)
                datum = Point(*case['segments'][0][:2])
                self.assertEqual(
                    [[point.X, point.Z] for point in points],
                    self.greedy_reference(datum, points))


if __name__ == '__main__':
    unittest.main()
