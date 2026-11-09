import math
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.op.groove import GrooveOP
from liblathe.tool.tool import Tool, ToolSide

# Part with a 10 mm wide groove to radius 10 and a 4 mm wide groove to radius 12
PART_POINTS = [(0, 0), (15, 0), (15, -10), (10, -10), (10, -20), (15, -20), (15, -26),
               (12, -26), (12, -30), (15, -30), (15, -40), (0, -40)]
TOOL_WIDTH = 2


def part_radius(z):
    if -20 < z < -10:
        return 10
    if -30 < z < -26:
        return 12
    return 15


def square_tool(width=TOOL_WIDTH, sign=1):
    """Square tool with its origin on the leading (+Z) corner of the cutting edge."""
    points = [(0, 0), (0, -width), (width, -width), (width, 0), (0, 0)]
    tool = Tool()
    tool.set_tool_shape('S')
    tool.set_tool_from_segments([Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                                 for a, b in zip(points, points[1:])])
    if sign < 0:
        tool.side = ToolSide.FAR
    return tool


def make_op(stock=(0, -40, 16, 0), sign=1, tool=None, **params):
    settings = {'step_over': 1.5, 'finish_passes': 0, 'stock_to_leave': 0, 'hfeed': 10}
    settings.update(params)
    op = GrooveOP()
    op.setParams(settings)
    xmin, zmin, xmax, zmax = stock
    if sign > 0:
        op.add_stock(BoundBox(Point(xmin, zmin), Point(xmax, zmax)))
    else:
        op.add_stock(BoundBox(Point(-xmax, zmin), Point(-xmin, zmax)))
    op.addPartSegments([Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
                        for a, b in zip(PART_POINTS, PART_POINTS[1:])])
    op.add_tool(tool or square_tool(sign=sign))
    return op


def passes(op):
    return [(seg.start.Z, seg.start.X, seg.end.X) for layer in op.tool_paths for seg in layer.getSegments()]


class test_GrooveOP(unittest.TestCase):
    """Tests for groove.py"""

    @classmethod
    def setUpClass(cls):
        cls.op = make_op()
        cls.gcode = cls.op.getGCode()

    def test_params(self):
        params = self.op.getParams()
        self.assertEqual(params['step_over'], 1.5)
        self.assertNotIn('overlap_percent', params)
        self.assertEqual(GrooveOP.overlap_percent, 10.0)
        self.assertNotIn('overlap_percent', vars(self.op))

    def test_invalid_params(self):
        for params in ({'step_over': 0}, {'step_over': -1}, {'step_over': math.nan},
                       {'step_over': math.inf}, {'finish_passes': -1}, {'finish_passes': 1.5},
                       {'finish_passes': True}):
            op = make_op(**params)
            op.tool_paths = ['stale']
            with self.assertRaises(ValueError):
                op.generatePath()
            self.assertEqual(op.tool_paths, [])

    def test_z_stations_are_even(self):
        stations = GrooveOP.get_z_stations(0, -10, 3)
        self.assertEqual(len(stations), 5)
        self.assertEqual(stations[0], 0)
        self.assertEqual(stations[-1], -10)
        for a, b in zip(stations, stations[1:]):
            self.assertAlmostEqual(a - b, 2.5)
        self.assertEqual(GrooveOP.get_z_stations(-5, -5, 3), [-5])

    def test_max_increment_scales_with_tool_width(self):
        op = make_op(step_over=10)
        self.assertAlmostEqual(op.get_max_increment(square_tool(2).get_segmentgroup().boundbox()), 1.8)
        self.assertAlmostEqual(op.get_max_increment(square_tool(4).get_segmentgroup().boundbox()), 3.6)
        op.step_over = 1
        self.assertAlmostEqual(op.get_max_increment(square_tool(4).get_segmentgroup().boundbox()), 3.6)

    def test_layers_are_depth_first(self):
        tops = []
        for layer in self.op.tool_paths:
            segments = layer.getSegments()
            starts = {round(seg.start.X, 6) for seg in segments}
            self.assertEqual(len(starts), 1, "each layer starts from a single depth")
            tops.append(starts.pop())
            zs = [seg.start.Z for seg in segments]
            self.assertEqual(zs, sorted(zs, reverse=True))
        self.assertEqual(tops, sorted(tops, reverse=True))
        self.assertEqual(len(tops), len(set(tops)))

    def test_passes_are_radial_and_within_limits(self):
        max_increment = self.op.get_max_increment(self.op.tool.get_segmentgroup().boundbox())
        for layer in self.op.tool_paths:
            for seg in layer.getSegments():
                self.assertEqual(seg.start.Z, seg.end.Z)
                self.assertLess(seg.end.X, seg.start.X)
                self.assertLessEqual(seg.start.X - seg.end.X, self.op.step_over + 1e-6)
                self.assertGreaterEqual(seg.end.X, 0)
        # stations in the deepest layer (the wide groove) are evenly spaced and below the tool width
        deep = [seg.start.Z for seg in self.op.tool_paths[-1].getSegments()]
        increments = [a - b for a, b in zip(deep, deep[1:])]
        self.assertGreater(len(increments), 1)
        self.assertTrue(all(0 < inc <= max_increment + 1e-6 for inc in increments))
        self.assertLess(max_increment, TOOL_WIDTH)
        self.assertLessEqual(max(increments) - min(increments), 1e-5)

    def check_removal(self, op, z_min, z_max):
        """All material in the range is removed within offset tolerance, one step-over at a time."""
        grid = [z_max - i * 0.005 for i in range(1, int((z_max - z_min) / 0.005))]
        floor = {z: op.stock.XMax for z in grid}
        for z, _, end in passes(op):
            self.assertGreaterEqual(z - TOOL_WIDTH, z_min - 1e-6)
            self.assertLessEqual(z, z_max + 1e-6)
            for zp in grid:
                if z - TOOL_WIDTH <= zp <= z:
                    cut_to = max(end, part_radius(zp))
                    self.assertLessEqual(floor[zp] - cut_to, op.step_over + 1e-6)
                    floor[zp] = min(floor[zp], cut_to)
        # leftover material wider than the offset tolerance would be a missed pass
        widest = run = 0
        for zp in grid:
            run = run + 0.005 if floor[zp] - part_radius(zp) > 0.06 else 0
            widest = max(widest, run)
        self.assertLessEqual(widest, 0.05)

    def test_full_part_removes_material(self):
        self.check_removal(self.op, -40, 0)
        self.assertLess(min(end for _, _, end in passes(self.op)), 10.05)

    def test_section_is_limited_to_stock_range(self):
        op = make_op(stock=(0, -20, 16, -10))
        op.generatePath()
        self.assertTrue(op.tool_paths)
        self.check_removal(op, -20, -10)

    def test_min_diameter_limits_depth(self):
        op = make_op(stock=(13, -40, 16, 0))
        op.generatePath()
        self.assertGreaterEqual(min(end for _, _, end in passes(op)), 13 - 1e-6)

    def test_stock_to_leave(self):
        op = make_op(stock=(0, -20, 16, -10), stock_to_leave=0.5)
        op.generatePath()
        self.assertAlmostEqual(min(end for _, _, end in passes(op)), 10.5, delta=0.05)

    def test_narrow_range_is_rejected(self):
        op = make_op(stock=(0, -11, 16, -10))
        with self.assertRaises(ValueError):
            op.generatePath()
        self.assertEqual(op.tool_paths, [])

    def test_gcode_moves(self):
        self.assertEqual(self.gcode[0].get_movement(), 'G18')
        moves = self.gcode[1:]
        x_clear = max(command.getParams()['X'] for command in moves)
        self.assertGreater(x_clear, self.op.stock.XMax)
        previous = None
        for command in moves:
            self.assertIsInstance(command, Command)
            self.assertIn(command.get_movement(), ('G0', 'G1'))
            params = command.getParams()
            self.assertEqual(params['F'], 10)
            if previous is not None and abs(params['Z'] - previous['Z']) > 1e-9:
                # Z only changes with a rapid while the tool is radially clear
                self.assertEqual(command.get_movement(), 'G0')
                self.assertAlmostEqual(params['X'], x_clear)
                self.assertAlmostEqual(previous['X'], x_clear)
            previous = params

    def test_far_side_mirrors_near_side(self):
        far = make_op(sign=-1).getGCode()
        self.assertEqual(len(far), len(self.gcode))
        for near_command, far_command in zip(self.gcode[1:], far[1:]):
            self.assertEqual(near_command.get_movement(), far_command.get_movement())
            self.assertAlmostEqual(near_command.getParams()['X'], -far_command.getParams()['X'], places=5)
            self.assertAlmostEqual(near_command.getParams()['Z'], far_command.getParams()['Z'], places=5)

    def test_finish_passes_are_repeated_contours_after_plunges(self):
        plunge_layers = len(self.op.tool_paths)
        for count in (0, 1, 2):
            with self.subTest(finish_passes=count):
                op = make_op(finish_passes=count)
                op.generatePath()
                self.assertEqual(len(op.tool_paths), plunge_layers + count)
                finishes = op.tool_paths[plunge_layers:]
                for finish in finishes:
                    self.assertEqual([(s.start.X, s.start.Z, s.end.X, s.end.Z) for s in finish.getSegments()],
                                     [(s.start.X, s.start.Z, s.end.X, s.end.Z) for s in finishes[0].getSegments()])
                    # follows the walls and floors, not only radial moves
                    self.assertTrue(any(abs(s.start.Z - s.end.Z) > 1 for s in finish.getSegments()))

    def test_finish_pass_stays_inside_grooving_limits(self):
        op = make_op(stock=(11, -20, 16, -10), finish_passes=1)
        op.generatePath()
        bounds = op.tool.get_segmentgroup().boundbox()
        z_high, z_low = op.get_z_range(bounds)
        for seg in op.tool_paths[-1].getSegments():
            for point in (seg.start, seg.end):
                self.assertGreaterEqual(point.X, 11 - 1e-6)
                self.assertLessEqual(point.X, 16 + 1e-6)
                self.assertLessEqual(point.Z, z_high + 1e-6)
                self.assertGreaterEqual(point.Z, z_low - 1e-6)

    def test_finish_pass_removes_sloped_wall_scallops(self):
        # 45 degree walls from radius 15 to a radius 10 floor
        points = [(0, 0), (15, 0), (15, -10), (10, -15), (10, -25), (15, -30), (15, -40), (0, -40)]

        def radius(z):
            return max(10, z + 25 if z > -15 else -z - 15)

        def leftover(op):
            grid = [-10 - i * 0.005 for i in range(1, 4000)]
            floor = [op.stock.XMax] * len(grid)
            for layer in op.tool_paths:
                for seg in layer.getSegments():
                    steps = max(1, int(seg.getLength() / 0.005))
                    for i in range(steps + 1):
                        origin = seg.start.lerp(seg.end, i / steps)
                        # the square tool cuts from its origin to TOOL_WIDTH in -Z at the origin radius
                        first = max(0, math.ceil((-10 - origin.Z) / 0.005) - 1)
                        last = min(len(grid), math.floor((-10 - origin.Z + TOOL_WIDTH) / 0.005))
                        for index in range(first, last):
                            floor[index] = min(floor[index], max(origin.X, radius(grid[index])))
            return max(f - radius(z) for f, z in zip(floor, grid))

        results = []
        for count in (0, 1):
            op = make_op(stock=(0, -30, 16, -10), finish_passes=count)
            op.partSegmentGroup = SegmentGroup()
            op.addPartSegments([Segment(Point(*a), Point(*b)) for a, b in zip(points, points[1:])])
            op.getGCode()
            results.append(leftover(op))
        self.assertGreater(results[0], 1)
        self.assertLess(results[1], 0.1)

    def test_finish_gcode_approaches_and_retracts_radially(self):
        op = make_op(finish_passes=1)
        gcode = op.getGCode()
        moves = [command.getParams() for command in gcode[1:]]
        x_clear = max(params['X'] for params in moves)
        for previous, current, command in zip(moves, moves[1:], gcode[2:]):
            if command.get_movement() == 'G0' and abs(current['Z'] - previous['Z']) > 1e-6:
                self.assertAlmostEqual(previous['X'], x_clear)
                self.assertAlmostEqual(current['X'], x_clear)


if __name__ == '__main__':
    unittest.main()
