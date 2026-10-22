import unittest
from unittest.mock import Mock, patch

import test_face_op
import test_partoff_op
import test_profile_op
import test_rough_op

from liblathe.base.segmentgroup import SegmentGroup


class test_PathRegeneration(unittest.TestCase):
    fixtures = (
        test_face_op.test_FaceOP,
        test_partoff_op.test_PartoffOP,
        test_profile_op.test_ProfileOP,
        test_rough_op.test_RoughOP,
    )

    def operation(self, fixture):
        case = fixture()
        case.setUp()
        return case.op

    def commands(self, operation):
        return [
            (command.get_movement(), command.getParams())
            for command in operation.getGCode()
        ]

    def paths(self, operation):
        if isinstance(operation, test_face_op.FaceOP):
            return operation.clearing_paths
        return operation.tool_paths

    def test_repeated_generation(self):
        for fixture in self.fixtures:
            with self.subTest(operation=fixture.__name__):
                operation = self.operation(fixture)
                expected = self.commands(operation)
                count = len(self.paths(operation))
                self.assertGreater(count, 0)
                for _ in range(2):
                    self.assertEqual(self.commands(operation), expected)
                    self.assertEqual(len(self.paths(operation)), count)

    def test_changed_parameters_replace_previous_paths(self):
        for fixture in self.fixtures:
            with self.subTest(operation=fixture.__name__):
                operation = self.operation(fixture)
                original = self.commands(operation)
                params = {'clearance': operation.clearance + 1, 'step_over': 2}
                operation.setParams(params)
                fresh = self.operation(fixture)
                fresh.setParams(params)
                expected = self.commands(fresh)
                self.assertNotEqual(expected, original)
                self.assertEqual(self.commands(operation), expected)
                self.assertEqual(len(self.paths(operation)), len(self.paths(fresh)))

    def test_failed_generation_publishes_no_partial_paths(self):
        for fixture, module in (
            (test_profile_op.test_ProfileOP, 'liblathe.op.profile'),
            (test_rough_op.test_RoughOP, 'liblathe.op.rough'),
        ):
            for method in ('getGCode', 'generatePath'):
                with self.subTest(operation=fixture.__name__, method=method):
                    operation = self.operation(fixture)
                    self.commands(operation)
                    self.assertTrue(operation.tool_paths)
                    intersection = Mock(side_effect=[False, True])

                    def group():
                        candidate = Mock(wraps=SegmentGroup())
                        candidate.intersectsGroup = intersection
                        return candidate

                    with patch(module + '.SegmentGroup', side_effect=group):
                        with self.assertRaisesRegex(ValueError, 'intersects part'):
                            getattr(operation, method)()

                    self.assertEqual(intersection.call_count, 2)
                    self.assertEqual(operation.tool_paths, [])
                    params = {'clearance': operation.clearance + 1, 'step_over': 2}
                    operation.setParams(params)
                    fresh = self.operation(fixture)
                    fresh.setParams(params)
                    self.assertEqual(self.commands(operation), self.commands(fresh))
                    self.assertEqual(len(operation.tool_paths), len(fresh.tool_paths))


if __name__ == '__main__':
    unittest.main()
