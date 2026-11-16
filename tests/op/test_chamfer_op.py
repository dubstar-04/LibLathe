import math
import unittest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.op.base import Direction, MachiningMode
from liblathe.op.chamfer import ChamferOP, ChamferPosition
from liblathe.tool.tool import Tool, ToolSide


class ChamferTests(unittest.TestCase):
    def operation(self, vertices=None, shift=(0, 0)):
        operation = ChamferOP()
        vertices = vertices or [(0, 0), (10, 0), (10, -20), (0, -20)]
        operation.addPartSegments([
            Segment(Point(*start), Point(*end))
            for start, end in zip(vertices, vertices[1:])])
        tool = Tool()
        outline = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
        tool.set_tool_from_segments([
            Segment(Point(start[0] - shift[0], start[1] - shift[1]),
                    Point(end[0] - shift[0], end[1] - shift[1]))
            for start, end in zip(outline, outline[1:])])
        operation.add_tool(tool)
        operation.add_containment(BoundBox(Point(0, -22), Point(15, 5)))
        operation.setParams({"chamfer_size": 1, "corner_indices": (1,)})
        return operation

    def test_equal_break_and_repeat_generation_preserve_original_part(self):
        operation = self.operation()
        operation.setParams({"pass_offset": 1.0})
        self.assertEqual(operation.direction, Direction.RADIAL)
        first = operation.getGCode()
        stroke = operation.tool_paths[0].getSegments()[0]
        self.assertAlmostEqual(stroke.start.X, 10, delta=0.001)
        self.assertAlmostEqual(stroke.start.Z, -1, delta=0.001)
        self.assertAlmostEqual(stroke.end.X, 9, delta=0.001)
        self.assertAlmostEqual(stroke.end.Z, 0, delta=0.001)
        self.assertEqual(len(operation.tool_paths), 1)
        second = operation.getGCode()
        self.assertEqual([command.to_string() for command in first],
                         [command.to_string() for command in second])
        self.assertTrue(operation.partSegmentGroup.getSegments()[0].end.isSame(Point(10, 0)))

    def test_compensation_tracks_insert_datum(self):
        original, shifted = self.operation(), self.operation(shift=(0.6, 0.8))
        original.setParams({"pass_offset": 0.2})
        shifted.setParams({"pass_offset": 0.2})
        original.generatePath()
        shifted.generatePath()
        self.assertEqual(len(original.tool_paths), 4)
        for first_group, second_group in zip(original.tool_paths, shifted.tool_paths):
            for name in ("start", "end"):
                first = getattr(first_group.getSegments()[0], name)
                second = getattr(second_group.getSegments()[0], name)
                self.assertAlmostEqual(second.X - first.X, 0.6, places=5)
                self.assertAlmostEqual(second.Z - first.Z, 0.8, places=5)

    def test_pass_offset_limits_normal_infeed_and_finishes_the_chamfer(self):
        depth = 1 / math.sqrt(2)
        for offset, expected_passes in ((1.0, 1), (depth, 1), (depth / 2, 2),
                                        (depth / 4, 4), (0.2, 4), (0.3, 3)):
            with self.subTest(offset=offset):
                operation = self.operation()
                operation.setParams({"pass_offset": offset})
                commands = operation.getGCode()
                strokes = [group.getSegments()[0] for group in operation.tool_paths]
                self.assertEqual(len(strokes), expected_passes)
                depths = [stroke.getLength() / 2 for stroke in strokes]
                self.assertAlmostEqual(depths[-1], depth, delta=1e-5)
                for index, current in enumerate(depths, 1):
                    self.assertAlmostEqual(current, depth * index / expected_passes, delta=1e-5)
                for previous, current in zip([0, *depths], depths):
                    self.assertGreater(current, previous)
                    self.assertLessEqual(current - previous, offset + 1e-5)
                moves = []
                previous = None
                for command in commands:
                    params = command.getParams()
                    if "X" not in params or "Z" not in params:
                        continue
                    current = Point(params["X"], params["Z"])
                    if command.get_movement() == "G1" and previous is not None:
                        moves.append((previous, current))
                    previous = current
                for stroke in strokes:
                    self.assertTrue(any(start.isSame(stroke.start) and end.isSame(stroke.end)
                                        for start, end in moves))
                if offset == 0.2:
                    repeated = operation.getGCode()
                    self.assertEqual([command.to_string() for command in commands],
                                     [command.to_string() for command in repeated])
                    self.assertEqual(len(operation.tool_paths), expected_passes)

    def test_external_chamfers_cut_from_radial_max_to_radial_min(self):
        for position in (ChamferPosition.FRONT, ChamferPosition.BACK):
            with self.subTest(position=position):
                operation = self.operation()
                operation.setParams({"chamfer_position": position})
                commands = operation.getGCode()
                self.assertEqual(operation.direction, Direction.RADIAL)
                for group in operation.tool_paths:
                    stroke = group.getSegments()[0]
                    self.assertGreater(stroke.start.X, stroke.end.X)
                    self.assertTrue(any(
                        previous.getParams().get("X") == stroke.start.X
                        and previous.getParams().get("Z") == stroke.start.Z
                        and current.get_movement() == "G1"
                        and current.getParams().get("X") == stroke.end.X
                        and current.getParams().get("Z") == stroke.end.Z
                        for previous, current in zip(commands, commands[1:])))

    def test_invalid_or_unrepresentable_pass_offsets_clear_paths(self):
        operation = self.operation()
        operation.getGCode()
        for offset in (0, -1, math.nan, math.inf, 1e-20, 1e-320):
            with self.subTest(offset=offset):
                operation.setParams({"pass_offset": offset})
                with self.assertRaisesRegex(ValueError, "pass_offset|precision"):
                    operation.getGCode()
                self.assertEqual(operation.tool_paths, [])
                self.assertEqual(operation.clearing_paths, [])

    def test_external_shoulder_chamfer_with_grooving_insert_cuts_inward(self):
        operation = self.operation([
            (0, 50), (3, 50), (5, 48), (5, 14), (4, 14),
            (4, 10), (10, 10), (10, 0), (0, 0)])
        operation.setParams({"corner_indices": (6,), "pass_offset": 0.25})
        operation.add_containment(BoundBox(Point(0, -20), Point(40, 30)))
        tool = Tool()
        radius = 0.2
        bulge = math.tan(math.pi / 8)
        tool.set_tool_from_segments([
            Segment(Point(radius, -2.7755575615628914e-17), Point(0, radius), bulge),
            Segment(Point(0, radius), Point(0, 2 - radius)),
            Segment(Point(0, 2 - radius), Point(radius, 2), bulge),
            Segment(Point(radius, 2), Point(12, 2)),
            Segment(Point(12, 2), Point(12, 0)),
            Segment(Point(12, 0), Point(radius, 0)),
        ])
        operation.add_tool(tool)
        commands = operation.getGCode()
        self.assertEqual(len(operation.tool_paths), 3)
        contact = radius - radius / math.sqrt(2)
        final = operation.tool_paths[-1].getSegments()[0]
        self.assertAlmostEqual(final.start.X + contact, 10, delta=0.001)
        self.assertAlmostEqual(final.start.Z + contact, 9, delta=0.001)
        self.assertAlmostEqual(final.end.X + contact, 9, delta=0.001)
        self.assertAlmostEqual(final.end.Z + contact, 10, delta=0.001)
        cuts = [
            (previous.getParams(), current.getParams())
            for previous, current in zip(commands, commands[1:])
            if current.get_movement() == "G1"
            and previous.getParams().get("Z") != current.getParams().get("Z")
            and previous.getParams().get("X") != current.getParams().get("X")
        ]
        self.assertEqual(len(cuts), 3)
        for start, end in cuts:
            self.assertGreater(start["X"], end["X"])

    def test_round_nose_support_is_not_an_endpoint_approximation(self):
        operation = self.operation()
        operation.setParams({"pass_offset": 0.2})
        tool = Tool()
        tool.set_tool_from_segments([
            Segment(Point(0, 0.5), Point(0.5, 0), -math.tan(math.pi / 8)),
            Segment(Point(0.5, 0), Point(2, 0)),
            Segment(Point(2, 0), Point(2, 2)),
            Segment(Point(2, 2), Point(0, 2)),
            Segment(Point(0, 2), Point(0, 0.5)),
        ])
        operation.add_tool(tool)
        operation.getGCode()
        self.assertEqual(len(operation.tool_paths), 4)
        stroke = operation.tool_paths[-1].getSegments()[0]
        contact = 0.5 - 0.5 / math.sqrt(2)
        self.assertAlmostEqual(stroke.end.X + contact, 9, delta=0.001)
        self.assertAlmostEqual(stroke.end.Z + contact, 0, delta=0.001)

    def test_multiple_selected_corners_and_all_feeds_stay_contained(self):
        operation = self.operation()
        operation.add_containment(BoundBox(Point(0, -25), Point(15, 5)))
        operation.corner_indices = (1, 2)
        operation.setParams({"pass_offset": 0.3})
        commands = operation.getGCode()
        self.assertEqual(len(operation.tool_paths), 6)
        limits = operation.containment
        for command in commands:
            if command.get_movement() == "G1":
                params = command.getParams()
                self.assertLessEqual(limits.XMin, params["X"])
                self.assertLessEqual(params["X"], limits.XMax)
                self.assertLessEqual(limits.ZMin, params["Z"])
                self.assertLessEqual(params["Z"], limits.ZMax)

    def test_internal_mouth_and_far_side_reflections(self):
        cases = [(internal, position) for internal in (False, True)
                 for position in (ChamferPosition.FRONT, ChamferPosition.BACK)]
        for internal, position in cases:
            with self.subTest(internal=internal, position=position):
                vertices = [(5, 0), (5, -20)] if internal else None
                near = self.operation(vertices)
                front_index = 0 if internal else 1
                near.corner_indices = (
                    front_index if position == ChamferPosition.FRONT else front_index + 1,)
                near.add_containment(BoundBox(Point(0, -25), Point(15, 5)))
                near.mode = MachiningMode.INTERNAL if internal else MachiningMode.EXTERNAL
                near.direction = Direction.RADIAL
                near.setParams({"pass_offset": 0.2, "chamfer_position": position})
                far = self.operation(vertices)
                far.corner_indices, far.mode, far.direction = near.corner_indices, near.mode, near.direction
                far.setParams({"pass_offset": near.pass_offset, "chamfer_position": position})
                far.partSegmentGroup = far.partSegmentGroup.reflectX()
                far.tool.segmentGroup = far.tool.get_segmentgroup().reflectX()
                far.tool.side = ToolSide.FAR
                far.add_containment(BoundBox(Point(-15, -25), Point(0, 5)))
                near_commands, far_commands = near.getGCode(), far.getGCode()
                self.assertEqual(len(near.tool_paths), 4)
                self.assertEqual(len(near_commands), len(far_commands))
                for operation in (near, far):
                    for group in operation.tool_paths:
                        stroke = group.getSegments()[0]
                        if internal:
                            self.assertLess(abs(stroke.start.X), abs(stroke.end.X))
                        else:
                            self.assertGreater(abs(stroke.start.X), abs(stroke.end.X))
                for first, second in zip(near_commands, far_commands):
                    self.assertEqual(first.get_movement(), second.get_movement())
                    if "X" in first.getParams():
                        self.assertAlmostEqual(first.getParams()["X"], -second.getParams()["X"], places=4)
                        self.assertAlmostEqual(first.getParams()["Z"], second.getParams()["Z"], places=4)
                if internal:
                    stroke = near.tool_paths[-1].getSegments()[0]
                    self.assertAlmostEqual(abs(stroke.end.X - stroke.start.X), 1, delta=0.001)
                    self.assertAlmostEqual(abs(stroke.end.Z - stroke.start.Z), 1, delta=0.001)

    def test_internal_chamfer_with_rounded_boring_insert_at_large_z(self):
        operation = self.operation([(15, 100), (15, 75), (0, 75)])
        operation.setParams({
            "mode": MachiningMode.INTERNAL, "corner_indices": (0,),
            "chamfer_size": 1, "pass_offset": 0.25, "clearance": 3,
        })
        vertices = [
            (-0.4985147714614868, 4.010517597198486, 0.36397022008895874),
            (-0.31670698523521423, 3.828709602355957, 0),
            (-0.0007610603934153914, 0.21743114292621613, 0.466307669878006),
            (-0.21743114292621613, 0.0007610603934153914, 0),
            (-3.828709602355957, 0.31670698523521423, 0.36397022008895874),
            (-4.010517597198486, 0.4985147714614868, 0),
            (-4.326463222503662, 4.109793186187744, 0.466307669878006),
            (-4.109793186187744, 4.326463222503662, 0),
        ]
        tool = Tool()
        tool.set_tool_from_segments([
            Segment(Point(x, z), Point(next_x, next_z), bulge)
            for (x, z, bulge), (next_x, next_z, _) in
            zip(vertices, vertices[1:] + vertices[:1])
        ])
        operation.add_tool(tool)
        operation.add_containment(BoundBox(Point(7.673537, 91.673537),
                                          Point(23.326463, 107.326463)))
        operation.add_stock(BoundBox(Point(0, 0), Point(50, 110)))
        commands = operation.getGCode()
        self.assertEqual(len(operation.tool_paths), 3)
        self.assertTrue(any(command.get_movement() == "G1" for command in commands))
        final = operation.tool_paths[-1].getSegments()[0]
        self.assertLess(final.start.X, final.end.X)
        self.assertAlmostEqual(abs(final.end.X - final.start.X), 1, delta=0.001)
        self.assertAlmostEqual(abs(final.end.Z - final.start.Z), 1, delta=0.001)

    def test_invalid_corners_sizes_and_containment_clear_paths(self):
        cases = [
            {"chamfer_size": value} for value in (0, -1, float("nan"), float("inf"), 10)
        ] + [{"corner_indices": indices} for indices in ((), (True,), (4,), (1, 1), (0,), None)]
        cases += [{"chamfer_position": value}
                  for value in (None, "Front", Direction.NEGATIVE_Z, 1)]
        for params in cases:
            with self.subTest(params=params):
                operation = self.operation()
                operation.getGCode()
                operation.setParams(params)
                with self.assertRaises(ValueError):
                    operation.getGCode()
                self.assertEqual(operation.tool_paths, [])
        operation = self.operation()
        operation.add_containment(BoundBox(Point(0, -22), Point(9.5, 5)))
        with self.assertRaisesRegex(ValueError, "complete compensated"):
            operation.getGCode()

    def test_concave_and_overlapping_breaks_rejected(self):
        operation = self.operation([(0, 0), (10, 0), (10, -2), (12, -2), (12, -20), (0, -20)])
        operation.corner_indices = (2,)
        with self.assertRaisesRegex(ValueError, "convex"):
            operation.getGCode()
        operation = self.operation([(0, 0), (10, 0), (10, -1.5), (0, -1.5)])
        operation.corner_indices = (1, 2)
        with self.assertRaisesRegex(ValueError, "overlap"):
            operation.getGCode()

    def test_insert_cannot_cut_an_unselected_shoulder(self):
        operation = self.operation(
            [(0, 0), (10, 0), (10, -2), (15, -2), (15, -20), (0, -20)])
        operation.add_containment(BoundBox(Point(0, -25), Point(25, 5)))
        operation.getGCode()
        tool = Tool()
        vertices = [(0, 0), (8, -8), (8, 2), (0, 0)]
        tool.set_tool_from_segments([
            Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
        operation.add_tool(tool)
        with self.assertRaises(RuntimeError):
            operation.getGCode()
        self.assertEqual(operation.tool_paths, [])
