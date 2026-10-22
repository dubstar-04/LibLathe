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

    def test_ordering_matches_pre_index_contours(self):
        for case in self.cases:
            with self.subTest(profile=case['name'], offset=case['offset']):
                group, points = self.extract(case)
                actual = [[point.X, point.Z] for point in points]
                self.assertEqual(actual, case['expected_points'])
                self.assertEqual(len(actual), len({tuple(point) for point in actual}))
                if case['expected_segments'] is not None:
                    result = group.offset(case['offset'])
                    self.assertEqual(
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
