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

    def axial_passes(self):
        passes = SegmentGroup()
        for z in (-5, -10):
            passes.addSegment(Segment(Point(12, z + 1), Point(12, z)))
        return passes

    def test_default_matches_explicit_auto(self):
        self.path.fromSegmentGroup(self.operation, self.passes, protect_part=True)
        explicit = Path()
        explicit.fromSegmentGroup(self.operation, self.passes, protect_part=True,
                                  direction=RoutingDirection.AUTO)
        self.assertEqual([command.to_string() for command in self.path.commands],
                         [command.to_string() for command in explicit.commands])

    def test_contained_feeds_and_stock_safe_rapids(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        self.path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True,
                                   contain_feeds=True)
        moves = self.path.commands[1:]
        tool = self.operation.tool.get_segmentgroup().boundbox()
        stock = self.operation.stock
        limits = self.operation.containment
        for previous, current in zip(moves, moves[1:]):
            start, end = previous.getParams(), current.getParams()
            if current.get_movement() == 'G1':
                for position in (start, end):
                    self.assertTrue(limits.XMin <= position['X'] <= limits.XMax)
                    self.assertTrue(limits.ZMin <= position['Z'] <= limits.ZMax)
            else:
                self.assertTrue(
                    min(start['X'], end['X']) + tool.XMin >= stock.XMax - 1e-5
                    or min(start['Z'], end['Z']) + tool.ZMin >= stock.ZMax - 1e-5
                    or max(start['Z'], end['Z']) + tool.ZMax <= stock.ZMin + 1e-5)
        self.assertEqual(moves[2].getParams()['Z'], limits.ZMax)

    def test_containment_inside_stock_rejects_outside_feed_entry_atomically(self):
        self.operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
        before = list(self.path.commands)
        with self.assertRaisesRegex(ValueError, "Enlarge containment"):
            self.path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True)
        self.assertEqual(self.path.commands, before)

    def test_radial_feed_entry_rejects_full_insert_collision_atomically(self):
        self.operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(10.2, -4), Point(10.2, -5)))
        before = list(self.path.commands)
        with self.assertRaisesRegex(ValueError, "Cannot approach"):
            self.path.fromSegmentGroup(self.operation, passes, protect_part=True,
                                       contain_feeds=True)
        self.assertEqual(self.path.commands, before)

    def test_radial_feed_entry_rejects_obstructing_shoulder_atomically(self):
        self.operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
        part = SegmentGroup()
        vertices = [(0, 0), (10, 0), (10, -3), (16, -3),
                    (16, -3.8), (10, -3.8), (10, -20), (0, -20)]
        for start, end in zip(vertices, vertices[1:]):
            part.addSegment(Segment(Point(*start), Point(*end)))
        self.operation.partSegmentGroup = part
        before = list(self.path.commands)
        with self.assertRaisesRegex(ValueError, "Cannot approach"):
            self.path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True,
                                       contain_feeds=True)
        self.assertEqual(self.path.commands, before)

    def test_contained_routing_can_use_radial_entry(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 1)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        self.path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True,
                                   contain_feeds=True)
        self.assertEqual(self.path.commands[3].getParams()['X'], 15)

    def test_roughing_rapids_move_one_axis_at_a_time(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        self.path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True,
                                   contain_feeds=True)
        moves = self.path.commands[1:]
        for previous, current in zip(moves, moves[1:]):
            if current.get_movement() == 'G0':
                start, end = previous.getParams(), current.getParams()
                self.assertTrue(abs(start['X'] - end['X']) < 1e-5
                                or abs(start['Z'] - end['Z']) < 1e-5)
        outside = moves[0].getParams()
        radial = moves[1].getParams()
        axial = moves[2].getParams()
        self.assertEqual(radial['Z'], outside['Z'])
        self.assertLess(radial['X'], outside['X'])
        self.assertEqual(axial['X'], radial['X'])
        self.assertEqual(axial['Z'], self.operation.containment.ZMax)

    def test_roughing_can_use_z_then_x_when_x_then_z_is_obstructed(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(12, -5), Point(11, -6)))

        def block_radial_at_axial_clearance(tool, start, end):
            if start.Z > 4 and end.Z == start.Z and end.X < start.X:
                raise RuntimeError("Radial transfer obstructed")
            return self.operation.partSegmentGroup._mock_wraps.validateToolSweep(tool, start, end)

        self.sweep.side_effect = block_radial_at_axial_clearance
        self.path.fromSegmentGroup(self.operation, passes, protect_part=True, contain_feeds=True)
        outside = self.path.commands[1].getParams()
        corner = self.path.commands[2].getParams()
        entry = self.path.commands[3].getParams()
        self.assertEqual(corner['X'], outside['X'])
        self.assertEqual(corner['Z'], entry['Z'])
        self.assertEqual(entry['X'], 15)
        self.assertEqual(entry['Z'], -2)

    def test_contained_routing_rejects_outside_cutting_segments(self):
        self.passes.addSegment(Segment(Point(13, -5), Point(12, -5)))
        with self.assertRaisesRegex(ValueError, "outside containment"):
            self.path.fromSegmentGroup(self.operation, self.passes, protect_part=True,
                                       contain_feeds=True)
        self.assertEqual(len(self.path.commands), 1)

    def test_extending_containment_extends_the_feed_approach(self):
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        for zmax in (2, 5):
            with self.subTest(zmax=zmax):
                self.operation.add_containment(BoundBox(Point(0, -22), Point(15, zmax)))
                path = Path()
                path.fromSegmentGroup(self.operation, self.axial_passes(), protect_part=True,
                                      contain_feeds=True)
                self.assertEqual(path.commands[3].getParams()['Z'], zmax)
                self.assertEqual(path.commands[4].get_movement(), 'G1')

    def test_contained_entry_follows_first_cut_direction(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(12, -5), Point(11, -6)))
        self.path.fromSegmentGroup(self.operation, passes, protect_part=True, contain_feeds=True)
        entry = self.path.commands[3].getParams()
        self.assertAlmostEqual(entry['X'], 15)
        self.assertAlmostEqual(entry['Z'], -2)

    def test_withdrawal_feeds_to_boundary_then_rapids_to_clearance(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(11, -5), Point(12, -4)))
        self.path.fromSegmentGroup(self.operation, passes, protect_part=True, contain_feeds=True)
        withdrawal = next(command for command in reversed(self.path.commands)
                          if command.get_movement() == 'G1')
        exit_point = withdrawal.getParams()
        self.assertAlmostEqual(exit_point['X'], 15, places=5)
        self.assertAlmostEqual(exit_point['Z'], -4)
        self.assertEqual(self.path.commands[-1].get_movement(), 'G0')

    def test_contained_entry_uses_safe_fallback_if_aligned_approach_is_blocked(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(12, -5), Point(11, -6)))

        def block_aligned(tool, start, end):
            if start.isSame(Point(15, -2)) and end.isSame(Point(12, -5)):
                raise RuntimeError("Aligned entry obstructed")
            return self.operation.partSegmentGroup._mock_wraps.validateToolSweep(tool, start, end)

        self.sweep.side_effect = block_aligned
        self.path.fromSegmentGroup(self.operation, passes, protect_part=True, contain_feeds=True)
        entry = self.path.commands[3].getParams()
        self.assertAlmostEqual(entry['X'], 12)
        self.assertAlmostEqual(entry['Z'], 4)

    def test_contained_exit_never_backtracks_when_outward_route_is_blocked(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(11, -4), Point(11, -6)))
        def block_outward(tool, start, end):
            if start.isSame(Point(11, -6)) and end.X > start.X:
                raise RuntimeError("Outward route obstructed")
            return self.operation.partSegmentGroup._mock_wraps.validateToolSweep(tool, start, end)

        self.sweep.side_effect = block_outward
        with self.assertRaisesRegex(ValueError, "Cannot retract"):
            self.path.fromSegmentGroup(self.operation, passes, protect_part=True, contain_feeds=True)
        self.assertEqual(len(self.path.commands), 1)

    def test_radial_cut_can_withdraw_axially_without_reversing_the_cut(self):
        self.operation.add_containment(BoundBox(Point(0, -22), Point(15, 4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(12, 1)))
        self.path.fromSegmentGroup(self.operation, self.passes, protect_part=True)
        moves = self.path.commands[1:]
        for previous, current in zip(moves, moves[1:]):
            a, b = previous.getParams(), current.getParams()
            if current.get_movement() == 'G1' and b['X'] > a['X']:
                self.fail("Automatic radial cut must not reverse along itself")

    def test_withdrawal_without_stock_clear_boundary_fails_atomically(self):
        self.operation.add_containment(BoundBox(Point(0, -20), Point(19.9487, 1.4)))
        self.operation.add_stock(BoundBox(Point(0, -20), Point(20, 1)))
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(19, 1.4), Point(19, -20)))
        with self.assertRaisesRegex(ValueError, "Cannot retract.*containment"):
            self.path.fromSegmentGroup(self.operation, passes, protect_part=True)
        self.assertEqual(len(self.path.commands), 1)

    def test_auto_prefers_cut_aligned_boundary_entry(self):
        self.route(RoutingDirection.AUTO)
        moves = self.path.commands[1:]
        first_feed = next(i for i, c in enumerate(moves) if c.get_movement() == 'G1')
        self.assertEqual(moves[first_feed - 1].getParams()['X'], moves[first_feed].getParams()['X'])
        self.assertEqual(moves[first_feed - 1].getParams()['X'], self.operation.containment.XMax)
        self.assertEqual(moves[first_feed - 1].getParams()['Z'], -5)
        self.assertTrue(self.sweep.called)

    def test_forced_directions_use_only_the_requested_axis(self):
        for direction in (RoutingDirection.RADIAL, RoutingDirection.AXIAL):
            with self.subTest(direction=direction):
                self.path = Path()
                self.sweep.reset_mock()
                self.route(direction)
                moves = self.path.commands[1:]
                for previous, current in zip(moves, moves[1:]):
                    if current.get_movement() != 'G1':
                        continue
                    start, end = previous.getParams(), current.getParams()
                    # The supplied cuts are radial; only approach/retract follow direction.
                    if any(start['X'] == s.start.X and start['Z'] == s.start.Z
                           and end['X'] == s.end.X and end['Z'] == s.end.Z
                           for s in self.passes.getSegments()):
                        continue
                    if direction == RoutingDirection.RADIAL:
                        self.assertAlmostEqual(start['Z'], end['Z'])
                    else:
                        self.assertAlmostEqual(start['X'], end['X'])

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
        passes = SegmentGroup()
        passes.addSegment(Segment(Point(12, -5), Point(11, -6)))
        for failure in ("entry", "exit"):
            with self.subTest(failure=failure):
                blocked = []

                def validate(tool, start, end):
                    entry = start.isSame(Point(12, -5)) and end.isSame(Point(12, -5))
                    exit = start.isSame(Point(11, -6)) and end.isSame(Point(12, -6))
                    if not blocked and (entry if failure == "entry" else exit):
                        blocked.append(True)
                        raise RuntimeError("Cannot certify sweep")
                    return self.operation.partSegmentGroup._mock_wraps.validateToolSweep(tool, start, end)

                self.sweep.side_effect = validate
                path = Path()
                path.fromSegmentGroup(self.operation, passes, protect_part=True)
                self.assertTrue(blocked)
                self.assertGreater(len(path.commands), 1)

    def test_forced_directions_fail_without_fallback_or_partial_commands(self):
        for direction in (RoutingDirection.RADIAL, RoutingDirection.AXIAL):
            for failure in ("entry", "exit"):
                with self.subTest(direction=direction, failure=failure):
                    def validate(tool, start, end):
                        entry = end.isSame(Point(12, -5))
                        exit = start.isSame(Point(10.5, -5))
                        if entry if failure == "entry" else exit:
                            raise RuntimeError("Cannot certify sweep")
                        return self.operation.partSegmentGroup._mock_wraps.validateToolSweep(tool, start, end)

                    self.sweep.side_effect = validate
                    before = list(self.path.commands)
                    with self.assertRaisesRegex(ValueError, 'Cannot approach|Cannot retract'):
                        self.route(direction)
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

    def test_feed_containment_cannot_be_disabled(self):
        with self.assertRaisesRegex(ValueError, "cannot be disabled"):
            self.path.fromSegmentGroup(self.operation, self.passes, contain_feeds=False)
        self.assertEqual(len(self.path.commands), 1)

    def test_arc_extents_outside_containment_fail_even_with_contained_endpoints(self):
        geometry = SegmentGroup()
        geometry.addSegment(Segment(Point(11, -5), Point(11, -10), 1))
        self.assertGreater(geometry.boundbox().XMax, self.operation.containment.XMax)
        with self.assertRaisesRegex(ValueError, "Cutting path is outside containment"):
            self.path.fromSegmentGroup(self.operation, geometry)
        self.assertEqual(len(self.path.commands), 1)

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
        with self.assertRaisesRegex(ValueError, 'Cannot approach.*containment'):
            path.fromSegmentGroup(self.operation, group, protect_part=True,
                                  direction=RoutingDirection.RADIAL, radial_clearance=15.5)
        self.assertEqual(len(path.commands), 1)

    def test_reversed_arc_uses_new_start_and_exchanges_g2_g3(self):
        self.operation.add_containment(BoundBox(Point(0, -20), Point(16, 3)))
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
