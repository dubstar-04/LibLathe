import unittest
from unittest.mock import Mock

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import Path, RoutingDirection
from liblathe.op.base import BaseOP
from liblathe.tool.tool import Tool


class test_Path(unittest.TestCase):
    def setUp(self):
        self.operation = BaseOP()
        self.operation.add_containment(BoundBox(Point(0, -20), Point(12, 1)))
        tool = Tool()
        vertices = [(-0.4, -0.4), (-0.4, 2), (2, 2), (2, -0.4), (-0.4, -0.4)]
        tool.set_tool_from_segments([
            Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
        self.operation.add_tool(tool)
        vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
        self.operation.addPartSegments([
            Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
        self.operation.partSegmentGroup = Mock(wraps=self.operation.partSegmentGroup)
        self.sweep = self.operation.partSegmentGroup.validateToolSweep
        self.passes = SegmentGroup()
        for z in (-5, -10):
            self.passes.addSegment(Segment(Point(12, z), Point(10.5, z)))
        self.path = Path()

    def route(self, direction):
        self.path.fromSegmentGroup(self.operation, self.passes, protect_part=True,
                                   direction=direction)

    def test_default_matches_explicit_auto(self):
        self.path.fromSegmentGroup(self.operation, self.passes, protect_part=True)
        explicit = Path()
        explicit.fromSegmentGroup(self.operation, self.passes, protect_part=True,
                                  direction=RoutingDirection.AUTO)
        self.assertEqual([command.to_string() for command in self.path.commands],
                         [command.to_string() for command in explicit.commands])

    def test_auto_prefers_axial_entry_and_radial_exit(self):
        self.route(RoutingDirection.AUTO)
        self.assertEqual(self.sweep.call_count, 4)
        for entry, retract in zip(self.sweep.call_args_list[::2], self.sweep.call_args_list[1::2]):
            _, start, end = entry.args
            self.assertAlmostEqual(start.X, end.X)
            _, start, end = retract.args
            self.assertAlmostEqual(start.Z, end.Z)

    def test_forced_directions_use_only_the_requested_axis(self):
        for direction in (RoutingDirection.RADIAL, RoutingDirection.AXIAL):
            with self.subTest(direction=direction):
                self.sweep.reset_mock()
                self.route(direction)
                self.assertEqual(self.sweep.call_count, 4)
                for call in self.sweep.call_args_list:
                    _, start, end = call.args
                    if direction == RoutingDirection.RADIAL:
                        self.assertAlmostEqual(start.Z, end.Z)
                    else:
                        self.assertAlmostEqual(start.X, end.X)

    def test_radial_repositions_z_only_at_radial_clearance(self):
        self.route(RoutingDirection.RADIAL)
        moves = self.path.commands[1:]
        x_clear = moves[0].getParams()['X']
        for previous, current in zip(moves, moves[1:]):
            start, end = previous.getParams(), current.getParams()
            if abs(start['Z'] - end['Z']) > 1e-6:
                self.assertEqual(current.get_movement(), 'G0')
                self.assertAlmostEqual(start['X'], x_clear)
                self.assertAlmostEqual(end['X'], x_clear)

    def test_axial_rapid_repositions_x_only_at_axial_clearance(self):
        self.route(RoutingDirection.AXIAL)
        moves = self.path.commands[1:]
        z_clear = moves[0].getParams()['Z']
        for previous, current in zip(moves, moves[1:]):
            start, end = previous.getParams(), current.getParams()
            if current.get_movement() == 'G0' and abs(start['X'] - end['X']) > 1e-6:
                self.assertAlmostEqual(start['Z'], z_clear)
                self.assertAlmostEqual(end['Z'], z_clear)

    def test_auto_can_fall_back_on_entry_and_exit(self):
        for failure in (0, 1):
            with self.subTest(failure=failure):
                self.sweep.reset_mock()
                results = [None] * 5
                results[failure] = RuntimeError('Cannot certify sweep')
                self.sweep.side_effect = results
                self.route(RoutingDirection.AUTO)
                self.assertEqual(self.sweep.call_count, 5)
                _, start, end = self.sweep.call_args_list[failure + 1].args
                if failure == 0:
                    self.assertAlmostEqual(start.Z, end.Z)
                else:
                    self.assertAlmostEqual(start.X, end.X)

    def test_forced_directions_fail_without_fallback_or_partial_commands(self):
        for direction in (RoutingDirection.RADIAL, RoutingDirection.AXIAL):
            for failure in (0, 1):
                with self.subTest(direction=direction, failure=failure):
                    self.sweep.reset_mock()
                    self.sweep.side_effect = [None] * failure + [RuntimeError('Cannot certify sweep')]
                    before = list(self.path.commands)
                    with self.assertRaisesRegex(ValueError, 'Cannot approach|Cannot retract'):
                        self.route(direction)
                    self.assertEqual(self.sweep.call_count, failure + 1)
                    self.assertEqual(self.path.commands, before)

    def test_forced_directions_stay_on_clearance_plane_between_passes(self):
        second = SegmentGroup()
        second.addSegment(Segment(Point(12, -15), Point(10.5, -15)))
        for direction, axis in ((RoutingDirection.RADIAL, 'X'), (RoutingDirection.AXIAL, 'Z')):
            with self.subTest(direction=direction):
                path = Path()
                for group in (self.passes, second):
                    path.fromSegmentGroup(self.operation, group, protect_part=True, direction=direction)
                moves = [command.getParams() for command in path.commands[1:]]
                outside = moves[0]
                # the outside-stock corner is only used to enter the path
                self.assertEqual(sum(1 for move in moves
                                     if abs(move['X'] - outside['X']) < 1e-9 and abs(move['Z'] - outside['Z']) < 1e-9), 1)
                other = 'Z' if axis == 'X' else 'X'
                for previous, current, command in zip(moves, moves[1:], path.commands[2:]):
                    if command.get_movement() == 'G0' and abs(previous[other] - current[other]) > 1e-6:
                        self.assertAlmostEqual(previous[axis], outside[axis])
                        self.assertAlmostEqual(current[axis], outside[axis])

    def test_auto_still_returns_to_outside_between_passes(self):
        self.route(RoutingDirection.AUTO)
        outside = self.path.commands[1].getParams()
        visits = [command for command in self.path.commands[1:]
                  if command.get_movement() == 'G0' and command.getParams() == outside]
        self.assertEqual(len(visits), 3)

    def test_invalid_direction_is_rejected(self):
        for direction in (None, 'Radial', 'Auto', 1):
            with self.subTest(direction=direction):
                with self.assertRaisesRegex(ValueError, 'RoutingDirection'):
                    self.route(direction)
                self.assertEqual(len(self.path.commands), 1)
        self.sweep.assert_not_called()

    def test_empty_group_emits_no_moves(self):
        self.passes = SegmentGroup()
        for direction in RoutingDirection:
            self.route(direction)
        self.assertEqual([command.to_string() for command in self.path.commands], ['G18'])
        self.sweep.assert_not_called()

    def test_local_clearance_rejects_unprotected_or_unsafe_routes_atomically(self):
        self.operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
        for settings in (
                {'direction': RoutingDirection.AUTO, 'radial_clearance': 15.4},
                {'direction': RoutingDirection.RADIAL, 'radial_clearance': float('nan')},
                {'direction': RoutingDirection.RADIAL, 'radial_clearance': 12},
                {'direction': RoutingDirection.RADIAL, 'return_to_clearance': True}):
            with self.subTest(settings=settings):
                path = Path()
                with self.assertRaises(ValueError):
                    path.fromSegmentGroup(self.operation, self.passes, protect_part=True, **settings)
                self.assertEqual(len(path.commands), 1)
        path = Path()
        with self.assertRaises(ValueError):
            path.fromSegmentGroup(self.operation, self.passes,
                                  direction=RoutingDirection.RADIAL, radial_clearance=15.4)
        self.assertEqual(len(path.commands), 1)

    def test_local_rapid_outside_prepared_region_is_rejected(self):
        self.operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
        group = SegmentGroup()
        group.addSegment(Segment(Point(12, -20), Point(10.5, -20)))
        path = Path()
        with self.assertRaisesRegex(ValueError, 'outside the prepared groove'):
            path.fromSegmentGroup(self.operation, group, protect_part=True,
                                  direction=RoutingDirection.RADIAL, radial_clearance=15.5)
        self.assertEqual(len(path.commands), 1)

    def test_reversed_arc_uses_new_start_and_exchanges_g2_g3(self):
        group = SegmentGroup()
        group.addSegment(Segment(Point(14, -5), Point(12, -7), 0.4))
        paths = []
        for geometry in (group, group.reversed()):
            path = Path()
            path.fromSegmentGroup(self.operation, geometry, direction=RoutingDirection.RADIAL)
            paths.append(path)
        forward = next(c for c in paths[0].commands if c.get_movement() == 'G3')
        backward = next(c for c in paths[1].commands if c.get_movement() == 'G2')
        self.assertAlmostEqual(forward.getParams()['X'], 12)
        self.assertAlmostEqual(backward.getParams()['X'], 14)
        arc = group.reversed().getSegments()[0]
        center = arc.getCentrePoint()
        self.assertAlmostEqual(backward.getParams()['I'], center.X - arc.start.X)
        self.assertAlmostEqual(backward.getParams()['K'], center.Z - arc.start.Z)


if __name__ == '__main__':
    unittest.main()
