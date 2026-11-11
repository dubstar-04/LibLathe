import math
import unittest
from unittest.mock import Mock, patch
from collections import Counter

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


def rounded_tool(width=2, radius=0.2, origin=0, sign=1):
    points = [(radius, 0), (0, radius), (0, width - radius),
              (radius, width), (12, width), (12, 0), (radius, 0)]
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(sign * a[0], a[1] + origin),
                Point(sign * b[0], b[1] + origin),
                sign * math.tan(math.pi / 8) if index in (0, 2) else 0)
        for index, (a, b) in enumerate(zip(points, points[1:]))])
    if sign < 0:
        tool.side = ToolSide.FAR
    return tool


def make_op(containment=(0, -40, 16, 0), sign=1, tool=None, **params):
    settings = {'pass_offset': 1.5, 'finish_passes': 0, 'stock_to_leave': 0, 'hfeed': 10}
    settings.update(params)
    op = GrooveOP()
    op.setParams(settings)
    xmin, zmin, xmax, zmax = containment
    if sign > 0:
        op.add_containment(BoundBox(Point(xmin, zmin), Point(xmax, zmax)))
    else:
        op.add_containment(BoundBox(Point(-xmax, zmin), Point(-xmin, zmax)))
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
        self.assertEqual(params['pass_offset'], 1.5)
        self.assertEqual(params['finish_pass_offset'], 0)
        self.assertNotIn('overlap_percent', params)
        self.assertEqual(GrooveOP.overlap_percent, 10.0)
        self.assertNotIn('overlap_percent', vars(self.op))

    def test_local_clearance_preserves_cuts_and_contains_feed_travel(self):
        op = make_op(containment=(0, -30, 8, -10), tool=rounded_tool(),
                     finish_passes=2, finish_pass_offset=0.1)
        points = [(0, 0), (14, 0), (14, -5), (8, -10), (5, -15),
                  (5, -25), (8, -30), (14, -35), (14, -40), (0, -40)]
        op.partSegmentGroup = SegmentGroup()
        op.addPartSegments([Segment(Point(*a), Point(*b)) for a, b in zip(points, points[1:])])
        op.generatePath()
        geometry = lambda: [[(s.start.X, s.start.Z, s.end.X, s.end.Z)
                              for s in g.getSegments()] for g in op.tool_paths]
        original = geometry()
        op.add_stock(BoundBox(Point(0, -45), Point(20, 5)))
        after = op.getGCode()
        self.assertEqual(geometry(), original)
        self.assertAlmostEqual(after[1].getParams()['X'], 23)
        first_feed = next(i for i, c in enumerate(after) if c.get_movement() == 'G1')
        self.assertAlmostEqual(after[first_feed - 1].getParams()['X'], 8)
        self.assertAlmostEqual(after[first_feed].getParams()['X'], 8)
        self.assertAlmostEqual(after[-1].getParams()['X'], 23)

        for a, b in zip(after[1:], after[2:]):
            if b.get_movement() == 'G1':
                for command in (a, b):
                    point = command.getParams()
                    self.assertTrue(op.containment.XMin - 1e-5 <= point['X'] <= op.containment.XMax + 1e-5)
                    self.assertTrue(op.containment.ZMin - 1e-5 <= point['Z'] <= op.containment.ZMax + 1e-5)
        bounds = op.tool.get_segmentgroup().boundbox()
        for a, b in zip(after[1:], after[2:]):
            start = Point(a.getParams()['X'], a.getParams()['Z'])
            end = Point(b.getParams()['X'], b.getParams()['Z'])
            if b.get_movement() == 'G0':
                op.partSegmentGroup.validateToolSweep(op.tool.get_segmentgroup(), start, end)
                inside_z = (min(start.Z, end.Z) + bounds.ZMin >= op.containment.ZMin - 1e-5
                            and max(start.Z, end.Z) + bounds.ZMax <= op.containment.ZMax + 1e-5)
                radial_limit = op.containment.XMax + bounds.XMin if inside_z else op.stock.XMax
                outside_radius = min(start.X, end.X) + bounds.XMin >= radial_limit - 1e-5
                outside_z = (min(start.Z, end.Z) + bounds.ZMin >= op.stock.ZMax - 1e-5
                             or max(start.Z, end.Z) + bounds.ZMax <= op.stock.ZMin + 1e-5)
                self.assertTrue(outside_radius or outside_z)

    def test_stock_validation(self):
        for bounds in (BoundBox(Point(0, 0), Point(0, 10)),
                       BoundBox(Point(0, 0), Point(10, 0)),
                       BoundBox(Point(0, 0), Point(math.inf, 10))):
            with self.subTest(bounds=bounds):
                with self.assertRaises(ValueError):
                    self.op.add_stock(bounds)
        for sign in (1, -1):
            op = make_op(sign=sign)
            op.add_stock(BoundBox(Point(0, -45), Point(-sign * 20, 5)))
            op.tool_paths = ['stale']
            with self.assertRaisesRegex(ValueError, 'signed radial'):
                op.getGCode()
            self.assertEqual(op.tool_paths, [])

    def test_fractional_local_clearance_does_not_return_to_stock_between_passes(self):
        op = make_op(containment=(0, -30, 30.8700008392334, -10),
                 tool=rounded_tool(), finish_passes=2)
        op.add_stock(BoundBox(Point(0, -45), Point(50.087928771972656, 5)))
        commands = op.getGCode()
        local = op._local_clearance()
        first_feed = next(i for i, c in enumerate(commands) if c.get_movement() == 'G1')
        # The final two rapids deliberately return to global clearance.
        for command in commands[first_feed:-2]:
            self.assertLessEqual(command.getParams()['X'], local + 1e-5)
        self.assertGreater(commands[-1].getParams()['X'], local + 1)

    def test_local_clearance_follows_radial_tool_reference(self):
        for shift in (-0.6, 0.6):
            with self.subTest(shift=shift):
                op = make_op(containment=(0, -20, 12, -10))
                op.generatePath()
                translated_paths = []
                for group in op.tool_paths:
                    translated = SegmentGroup()
                    for segment in group.getSegments():
                        translated.addSegment(Segment(
                            Point(segment.start.X + shift, segment.start.Z),
                            Point(segment.end.X + shift, segment.end.Z), segment.bulge))
                    translated_paths.append(translated)
                op.tool_paths = translated_paths
                original = op.tool.get_segmentgroup().getSegments()
                tool = Tool()
                tool.set_tool_from_segments([
                    Segment(Point(s.start.X - shift, s.start.Z),
                            Point(s.end.X - shift, s.end.Z), s.bulge) for s in original])
                op.add_tool(tool)
                op.add_containment(BoundBox(Point(shift, -20), Point(12 + shift, -10)))
                op.add_stock(BoundBox(Point(0, -45), Point(20, 5)))
                commands = op.generateGCode()
                first_feed = next(i for i, c in enumerate(commands) if c.get_movement() == 'G1')
                self.assertAlmostEqual(commands[first_feed - 1].getParams()['X'], 12 + shift, places=5)
                self.assertGreater(op._local_clearance(), 12 + shift)

    def test_local_clearance_mirrors_tools_and_nose_references(self):
        for origin in (-2, -1, 0):
            for clearance in (0, 0.1, 3):
                with self.subTest(origin=origin, clearance=clearance):
                    operations = []
                    for sign in (1, -1):
                        op = make_op(containment=(11, -20, 12, -10),
                                     tool=rounded_tool(origin=origin, sign=sign), sign=sign,
                                     finish_passes=2, finish_pass_offset=0.1, clearance=clearance)
                        op.add_stock(BoundBox(Point(0, -45), Point(sign * 20, 5)))
                        commands = op.getGCode()
                        self.assertTrue(commands)
                        operations.append(commands)
                    for near, far in zip(*operations):
                        self.assertEqual(near.get_movement(), far.get_movement())
                        if 'X' in near.getParams():
                            self.assertAlmostEqual(near.getParams()['X'], -far.getParams()['X'])
                            self.assertAlmostEqual(near.getParams()['Z'], far.getParams()['Z'])
                    self.assertEqual(len(operations[0]), len(operations[1]))

    def test_local_clearance_falls_back_when_transfer_crosses_a_shoulder(self):
        op = make_op(containment=(0, -25, 12, -5), clearance=0.5)
        op.add_stock(BoundBox(Point(0, -45), Point(20, 5)))
        op.partSegmentGroup = SegmentGroup().fromPoints([
            Point(0, 0), Point(10, 0), Point(10, -16), Point(14, -16),
            Point(14, -18), Point(10, -18), Point(10, -40), Point(0, -40)])
        group = SegmentGroup()
        for z in (-10, -22):
            group.addSegment(Segment(Point(12, z), Point(10.5, z)))
        op.tool_paths = [group]
        self.assertAlmostEqual(op._local_clearance(), 20.5)
        commands = op.generateGCode()
        for a, b in zip(commands[1:], commands[2:]):
            if b.get_movement() == 'G0':
                op.partSegmentGroup.validateToolSweep(
                    op.tool.get_segmentgroup(),
                    Point(a.getParams()['X'], a.getParams()['Z']),
                    Point(b.getParams()['X'], b.getParams()['Z']))

    def test_local_clearance_outside_prepared_z_uses_stock(self):
        op = make_op(containment=(0, -20, 12, -10))
        op.add_stock(BoundBox(Point(0, -45), Point(20, 5)))
        group = SegmentGroup()
        # The insert extends below the selected Z range.
        group.addSegment(Segment(Point(16, -19), Point(15.5, -19)))
        op.tool_paths = [group]
        self.assertAlmostEqual(op._local_clearance(), 23)

    def test_uncertified_local_transfer_leaves_no_paths(self):
        op = make_op(containment=(0, -20, 12, -10))
        op.add_stock(BoundBox(Point(0, -45), Point(20, 5)))
        op.generatePath()
        part = op.partSegmentGroup
        op.partSegmentGroup = Mock(wraps=part)

        def validate(tool, start, end):
            if start.Z != end.Z:
                raise RuntimeError("Cannot certify rapid")
            return part.validateToolSweep(tool, start, end)

        op.partSegmentGroup.validateToolSweep.side_effect = validate
        with self.assertRaisesRegex(ValueError, "Cannot approach.*containment"):
            op.generateGCode()
        self.assertEqual(op.tool_paths, [])

    def test_invalid_params(self):
        for params in ({'pass_offset': 0}, {'pass_offset': -1}, {'pass_offset': math.nan},
                       {'pass_offset': math.inf}, {'finish_passes': -1}, {'finish_passes': 1.5},
                       {'finish_passes': True}, {'finish_pass_offset': -0.1},
                       {'finish_pass_offset': math.nan}, {'finish_pass_offset': math.inf},
                       {'finish_pass_offset': -math.inf},
                       {'finish_passes': 3, 'finish_pass_offset': 1e308}):
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
        op = make_op(pass_offset=10)
        self.assertAlmostEqual(op.get_max_increment(square_tool(2).get_segmentgroup().boundbox()), 1.8)
        self.assertAlmostEqual(op.get_max_increment(square_tool(4).get_segmentgroup().boundbox()), 3.6)
        op.pass_offset = 1
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
                self.assertLessEqual(seg.start.X - seg.end.X, self.op.pass_offset + 1e-6)
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
        floor = {z: op.containment.XMax for z in grid}
        for z, _, end in passes(op):
            self.assertGreaterEqual(z - TOOL_WIDTH, z_min - 1e-6)
            self.assertLessEqual(z, z_max + 1e-6)
            for zp in grid:
                if z - TOOL_WIDTH <= zp <= z:
                    cut_to = max(end, part_radius(zp))
                    self.assertLessEqual(floor[zp] - cut_to, op.pass_offset + 1e-6)
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
        op = make_op(containment=(0, -20, 16, -10))
        op.generatePath()
        self.assertTrue(op.tool_paths)
        self.check_removal(op, -20, -10)

    def test_min_diameter_limits_depth(self):
        op = make_op(containment=(13, -40, 16, 0))
        op.generatePath()
        self.assertGreaterEqual(min(end for _, _, end in passes(op)), 13 - 1e-6)

    def test_stock_to_leave(self):
        op = make_op(containment=(0, -20, 16, -10), stock_to_leave=0.5)
        op.generatePath()
        self.assertAlmostEqual(min(end for _, _, end in passes(op)), 10.5, delta=0.05)

    def test_narrow_range_is_rejected(self):
        op = make_op(containment=(0, -11, 16, -10))
        with self.assertRaises(ValueError):
            op.generatePath()
        self.assertEqual(op.tool_paths, [])

    def test_gcode_moves(self):
        self.assertEqual(self.gcode[0].get_movement(), 'G18')
        moves = self.gcode[1:]
        x_clear = max(command.getParams()['X'] for command in moves)
        self.assertGreater(x_clear, self.op.containment.XMax)
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
        once = make_op(finish_passes=1)
        once.generatePath()
        strokes = once.tool_paths[plunge_layers:]
        self.assertGreater(len(strokes), 1)
        geometry = lambda group: [(s.start.X, s.start.Z, s.end.X, s.end.Z)
                                  for s in group.getSegments()]
        for count in (0, 1, 2):
            with self.subTest(finish_passes=count):
                op = make_op(finish_passes=count)
                op.generatePath()
                self.assertEqual(len(op.tool_paths), plunge_layers + count * len(strokes))
                finishes = op.tool_paths[plunge_layers:]
                self.assertEqual([geometry(group) for group in finishes],
                                 [geometry(group) for group in strokes] * count)
                for finish in finishes:
                    for segment in finish.getSegments():
                        self.assertLessEqual(segment.end.X, segment.start.X)

    def test_finish_strokes_preserve_all_segments_and_gaps(self):
        cases = [
            [],
            [(15, 0), (10, -5)],
            [(10, 0), (15, -5)],
            [(10, 0), (10, -5), (10, -10)],
            [(15, 0), (10, -5), (10, -10), (15, -15)],
            [(15, 0), (15, -1), (12, -3), (10, -5), (12, -7), (15, -9)],
            [(15, 0), (10, -5), (15, -10), (12, -15), (12, -16), (15, -20)],
            [(10, 0), (10.00001, -1), (10, -2), (10.00001, -3)],
        ]
        def edge_key(segment):
            return tuple(sorted(((segment.start.X, segment.start.Z),
                                 (segment.end.X, segment.end.Z))))

        for points in cases:
            for gap in (False, True):
                with self.subTest(points=points, gap=gap):
                    finish = SegmentGroup()
                    for a, b in zip(points, points[1:]):
                        finish.addSegment(Segment(Point(*a), Point(*b)))
                    if gap:
                        finish.addSegment(Segment(Point(20, -40), Point(18, -45)))
                    before = Counter(edge_key(s) for s in finish.getSegments())
                    strokes = GrooveOP._get_finish_strokes(finish)
                    after = Counter(edge_key(s) for group in strokes for s in group.getSegments())
                    self.assertEqual(before, after)
                    for stroke in strokes:
                        segments = stroke.getSegments()
                        for segment in segments:
                            self.assertLessEqual(segment.end.X, segment.start.X)
                        for a, b in zip(segments, segments[1:]):
                            self.assertTrue(a.end.isSame(b.start))

    def test_finish_pass_offset_reserves_allowance_and_reaches_final_contour(self):
        op = make_op(containment=(0, -20, 16, -10), finish_passes=3,
                     finish_pass_offset=0.1, stock_to_leave=0.3)
        contours = []
        split = op._get_finish_strokes

        def capture(contour):
            strokes = split(contour)
            contours.append(strokes)
            return strokes

        with patch.object(op, '_get_finish_strokes', side_effect=capture):
            op.getGCode()
        self.assertEqual(len(contours), 3)
        depths = [min(s.end.X for group in contour for s in group.getSegments())
                  for contour in contours]
        for actual, expected in zip(depths, (10.51, 10.41, 10.31)):
            self.assertAlmostEqual(actual, expected, delta=op.offset_tolerance)
        for outer, inner in zip(depths, depths[1:]):
            self.assertAlmostEqual(outer - inner, 0.1, delta=1e-5)
        finishing_count = sum(len(contour) for contour in contours)
        plunges = op.tool_paths[:-finishing_count]
        self.assertTrue(plunges)
        self.assertAlmostEqual(min(s.end.X for group in plunges for s in group.getSegments()),
                               depths[0], delta=0.001)
        final = make_op(containment=(0, -20, 16, -10), finish_passes=1, stock_to_leave=0.3)
        final.getGCode()
        self.assertEqual(
            [[(s.start.X, s.start.Z, s.end.X, s.end.Z) for s in group.getSegments()]
             for group in contours[-1]],
            [[(s.start.X, s.start.Z, s.end.X, s.end.Z) for s in group.getSegments()]
             for group in final.tool_paths[-len(contours[-1]):]])
        for layer in op.tool_paths:
            for segment in layer.getSegments():
                op.partSegmentGroup.validateToolSweep(
                    op.tool.get_segmentgroup(), segment.start, segment.end)

    def test_finish_pass_offset_zero_or_single_pass_preserves_gcode(self):
        for count in (0, 1, 3):
            reference = make_op(finish_passes=count).getGCode()
            op = make_op(finish_passes=count, finish_pass_offset=0 if count > 1 else 0.1)
            self.assertEqual([c.to_string() for c in op.getGCode()],
                             [c.to_string() for c in reference])

    def test_finish_pass_offset_uses_independent_normal_offsets(self):
        points = [(0, 0), (15, 0), (15, -10), (10, -15),
                  (10, -25), (15, -30), (15, -40), (0, -40)]
        for curved in (False, True):
            for sign in (1, -1):
                with self.subTest(curved=curved, sign=sign):
                    op = make_op(tool=rounded_tool(sign=sign), sign=sign,
                                 containment=(11, -30, 16, -10),
                                 finish_passes=3, finish_pass_offset=0.1)
                    op.partSegmentGroup = SegmentGroup()
                    op.addPartSegments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]),
                                sign * math.tan(math.pi / 8) if curved and i in (2, 4) else 0)
                        for i, (a, b) in enumerate(zip(points, points[1:]))])
                    profile = op.partSegmentGroup
                    if sign == 1:
                        # Observe offsets on the original tool-origin contour, never on a prior offset.
                        op.partSegmentGroup = Mock(wraps=profile)
                        generated = profile.defeature(op.containment, op.tool.get_segmentgroup(), True)
                        contour = Mock(wraps=generated)
                        op.partSegmentGroup.defeature.return_value = contour
                    commands = op.getGCode()
                    self.assertTrue(commands)
                    if sign == 1:
                        self.assertEqual(len(contour.offset.call_args_list), 4)
                        for call, expected in zip(contour.offset.call_args_list,
                                                  (-0.1, 0.21, 0.11, 0.01)):
                            self.assertAlmostEqual(call.args[0], expected)
                    bounds = op.tool.get_segmentgroup().boundbox()
                    z_high = op.containment.ZMax - bounds.ZMax
                    z_low = op.containment.ZMin - bounds.ZMin
                    for layer in op.tool_paths:
                        for segment in layer.getSegments():
                            self.assertLessEqual(sign * (segment.end.X - segment.start.X), 0)
                            for point in (segment.start, segment.end):
                                self.assertGreaterEqual(sign * point.X, 11 - 1e-5)
                                self.assertLessEqual(sign * point.X, 16 + 1e-5)
                                self.assertGreaterEqual(point.Z, z_low - 1e-5)
                                self.assertLessEqual(point.Z, z_high + 1e-5)
                            profile.validateToolSweep(
                                op.tool.get_segmentgroup(), segment.start, segment.end)

    def test_failed_later_finish_offset_leaves_no_paths(self):
        op = make_op(finish_passes=3, finish_pass_offset=0.1)
        part = op.partSegmentGroup
        contour = part.defeature(op.containment, op.tool.get_segmentgroup(), True)
        observed = Mock(wraps=contour)

        def offset(value):
            if abs(value - 0.11) < 1e-6:
                raise RuntimeError("Cannot offset later finishing contour")
            return contour.offset(value)

        observed.offset.side_effect = offset
        op.partSegmentGroup = Mock(wraps=part)
        op.partSegmentGroup.defeature.return_value = observed
        op.tool_paths = ['stale']
        with self.assertRaisesRegex(RuntimeError, 'later finishing contour'):
            op.generatePath()
        self.assertEqual(op.tool_paths, [])

    def test_finish_strokes_keep_floor_with_inward_wall(self):
        finish = SegmentGroup().fromPoints([
            Point(15, 0), Point(10, -5), Point(10, -10), Point(15, -15)])
        strokes = GrooveOP._get_finish_strokes(finish)
        self.assertEqual([stroke.count() for stroke in strokes], [2, 1])
        self.assertTrue(strokes[0].getSegments()[-1].end.isSame(Point(10, -10)))
        self.assertTrue(strokes[1].getSegments()[0].start.isSame(Point(15, -15)))

    def test_curved_walls_finish_inward_with_rounded_tool_and_mirrored_origins(self):
        points = [(0, 0), (15, 0), (15, -10), (10, -15),
                  (10, -25), (15, -30), (15, -40), (0, -40)]
        for origin in (-2, -1, 0):
            for sign in (1, -1):
                with self.subTest(origin=origin, sign=sign):
                    tool = rounded_tool(origin=origin, sign=sign)
                    op = make_op(tool=tool, sign=sign, containment=(0, -30, 16, -10),
                                 finish_passes=1, stock_to_leave=0.1)
                    op.partSegmentGroup = SegmentGroup()
                    op.addPartSegments([
                        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]),
                                sign * math.tan(math.pi / 8) if i in (2, 4) else 0)
                        for i, (a, b) in enumerate(zip(points, points[1:]))])
                    commands = op.getGCode()
                    self.assertTrue(commands)
                    # The otherwise identical zero-finish operation identifies the plunge prefix.
                    op.finish_passes = 0
                    op.getGCode()
                    plunge_count = len(op.tool_paths)
                    op.finish_passes = 1
                    op.getGCode()
                    self.assertGreater(len(op.tool_paths), plunge_count)
                    for stroke in op.tool_paths[plunge_count:]:
                        for segment in stroke.getSegments():
                            self.assertLessEqual(sign * (segment.end.X - segment.start.X), 0)
                            op.partSegmentGroup.validateToolSweep(
                                tool.get_segmentgroup(), segment.start, segment.end)

    def test_uncertified_finish_leaves_no_paths(self):
        op = make_op(finish_passes=1)
        part = op.partSegmentGroup
        op.partSegmentGroup = Mock(wraps=part)
        def validate(tool, moves):
            if any(abs(end.Z - start.Z) > 1e-6 for start, end in moves):
                raise RuntimeError("Uncertified finishing move")
            return part.validateToolSweeps(tool, moves)
        op.partSegmentGroup.validateToolSweeps.side_effect = validate
        with self.assertRaisesRegex(RuntimeError, 'Uncertified finishing'):
            op.getGCode()
        self.assertEqual(op.tool_paths, [])

    def test_failed_finish_routing_leaves_no_paths(self):
        op = make_op(finish_passes=1)
        op.generatePath()
        with patch('liblathe.op.base.Path.fromSegmentGroup',
                   side_effect=ValueError("Cannot approach")):
            with self.assertRaisesRegex(ValueError, 'Cannot approach'):
                op.generateGCode()
        self.assertEqual(op.tool_paths, [])

    def test_finish_pass_stays_inside_grooving_limits(self):
        op = make_op(containment=(11, -20, 16, -10), finish_passes=1)
        op.generatePath()
        bounds = op.tool.get_segmentgroup().boundbox()
        z_high, z_low = op.get_z_range(bounds)
        plunge = make_op(containment=(11, -20, 16, -10))
        plunge.generatePath()
        for seg in (s for group in op.tool_paths[len(plunge.tool_paths):]
                    for s in group.getSegments()):
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
            floor = [op.containment.XMax] * len(grid)
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
            op = make_op(containment=(0, -30, 16, -10), finish_passes=count)
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

    def test_each_finish_stroke_routes_via_radial_clearance(self):
        op = make_op(finish_passes=2)
        op.generatePath()
        plunged = make_op()
        plunged.generatePath()
        strokes = op.tool_paths[len(plunged.tool_paths):]
        self.assertGreater(len(strokes), 2)
        op.tool_paths = strokes
        commands = op.generateGCode()[1:]
        feeds = [(a, b) for a, b in zip(commands, commands[1:]) if b.get_movement() == 'G1']
        for stroke in strokes:
            segments = stroke.getSegments()
            for segment in segments:
                self.assertTrue(any(
                    abs(a.getParams()['X'] - segment.start.X) < 1e-5
                    and abs(a.getParams()['Z'] - segment.start.Z) < 1e-5
                    and abs(b.getParams()['X'] - segment.end.X) < 1e-5
                    and abs(b.getParams()['Z'] - segment.end.Z) < 1e-5 for a, b in feeds))
        for a, b in feeds:
            for command in (a, b):
                p = command.getParams()
                self.assertTrue(op.containment.XMin - 1e-5 <= p['X'] <= op.containment.XMax + 1e-5)
                self.assertTrue(op.containment.ZMin - 1e-5 <= p['Z'] <= op.containment.ZMax + 1e-5)


if __name__ == '__main__':
    unittest.main()
