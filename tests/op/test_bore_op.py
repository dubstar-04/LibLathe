import math
from unittest.mock import patch

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.op.bore import BoreOP
from liblathe.op.base import CutDirection
from liblathe.tool.tool import Tool, ToolSide


def operation(blind=False, sign=1):
    op = BoreOP()
    vertices = [(10, 0), (10, -20)]
    if blind:
        vertices.append((0, -20))
    op.addPartSegments([
        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
        for a, b in zip(vertices, vertices[1:])])
    vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(sign * a[0], a[1]), Point(sign * b[0], b[1]))
        for a, b in zip(vertices, vertices[1:])])
    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
    op.add_tool(tool)
    op.add_containment(BoundBox(Point(0, -20), Point(sign * 15, 3)))
    op.pass_offset = 0.5
    op.finish_passes = 3
    op.stock_to_leave = 0.2
    return op


def geometry(op):
    return [[(s.start.X, s.start.Z, s.end.X, s.end.Z, s.bulge)
             for s in g.getSegments()] for g in op.tool_paths]


@pytest.mark.parametrize("blind", [False, True])
def test_internal_allowance_and_pass_order(blind):
    op = operation(blind)
    op.generatePath()
    assert len(op.tool_paths) == 3
    for index, group in enumerate(op.tool_paths):
        allowance = op.stock_to_leave + (2 - index) * op.pass_offset
        edges = group.reversed().getSegments()
        wall = edges[0]
        assert wall.start.X == pytest.approx(10 - allowance - 0.01, abs=0.05)
        assert wall.end.X == pytest.approx(10 - allowance - 0.01, abs=0.05)
        assert wall.start.Z == pytest.approx(0, abs=1e-5)
        if blind:
            floor = edges[-1]
            assert floor.start.Z == pytest.approx(-20 + allowance + 0.01, abs=0.05)
            assert floor.end.Z == pytest.approx(-20 + allowance + 0.01, abs=0.05)
            assert floor.end.X == pytest.approx(0, abs=1e-5)
        else:
            assert wall.end.Z == pytest.approx(-20, abs=1e-5)
        for edge in edges:
            for point in (edge.start, edge.end):
                assert -1e-5 <= point.X <= 15 + 1e-5
                assert -20 - 1e-5 <= point.Z <= 1e-5


def test_feed_moves_are_contained_and_rapids_use_bore_clearance():
    op = operation()
    commands = op.getGCode()
    moves = commands[1:]
    assert moves[0].get_movement() == "G0"
    assert moves[0].getParams()["Z"] == op.containment.ZMax + op.clearance
    assert moves[-1].getParams()["Z"] == op.containment.ZMax + op.clearance
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() == "G1":
            for command in (previous, current):
                params = command.getParams()
                assert op.containment.XMin - 1e-5 <= params["X"] <= op.containment.XMax + 1e-5
                assert op.containment.ZMin - 1e-5 <= params["Z"] <= op.containment.ZMax + 1e-5
    for group in op.tool_paths:
        for edge in group.getSegments():
            assert any(a.getParams()["X"] == edge.start.X
                       and a.getParams()["Z"] == edge.start.Z
                       and b.getParams()["X"] == edge.end.X
                       and b.getParams()["Z"] == edge.end.Z
                       for a, b in zip(moves, moves[1:]))
    # Stock is not used to approve access, and no existing hole is required.
    op.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
    assert [c.to_string() for c in op.getGCode()] == [c.to_string() for c in commands]


@pytest.mark.parametrize("blind", [False, True])
def test_far_side_is_reflection_not_a_different_internal_strategy(blind):
    near, far = operation(blind), operation(blind, -1)
    a, b = near.getGCode(), far.getGCode()
    assert len(a) == len(b)
    for first, second in zip(a, b):
        assert first.get_movement() == second.get_movement()
        if "X" in first.getParams():
            assert first.getParams()["X"] == pytest.approx(-second.getParams()["X"])
            assert first.getParams()["Z"] == second.getParams()["Z"]


def test_tool_reference_translation_changes_origin_not_finished_wall():
    op = operation()
    original = geometry_after_generation(op)
    dx, dz = 0.6, 0.8
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(s.start.X - dx, s.start.Z - dz),
                Point(s.end.X - dx, s.end.Z - dz), s.bulge)
        for s in op.tool.get_segmentgroup().getSegments()])
    op.add_tool(tool)
    op.add_containment(BoundBox(Point(dx, -20 + dz), Point(15 + dx, dz)))
    op.generatePath()
    for expected, actual in zip(original, geometry(op)):
        assert actual[0][0] - dx == pytest.approx(expected[0][0], abs=0.05)
        assert actual[-1][3] - dz == pytest.approx(expected[-1][3], abs=0.05)


def geometry_after_generation(op):
    op.generatePath()
    return geometry(op)


def test_taper_and_curved_wall_use_existing_defeature_and_offsets():
    op = operation()
    op.partSegmentGroup = type(op.partSegmentGroup)()
    op.addPartSegments([
        Segment(Point(12, 0), Point(12, -5)),
        Segment(Point(12, -5), Point(10, -10), math.tan(math.pi / 16)),
        Segment(Point(10, -10), Point(9, -15)),
        Segment(Point(9, -15), Point(9, -20))])
    op.finish_passes = 1
    op.getGCode()
    points = [p for group in op.tool_paths for edge in group.getSegments()
              for p in (edge.start, edge.end)]
    assert points
    assert max(p.X for p in points) > 11.7
    assert min(p.X for p in points) < 8.9


def test_partial_containment_and_repeated_generation():
    op = operation()
    op.add_containment(BoundBox(Point(8, -15), Point(10, -5)))
    op.generatePath()
    expected = geometry(op)
    op.generatePath()
    assert expected == geometry(op)
    for group in op.tool_paths:
        for edge in group.getSegments():
            for p in (edge.start, edge.end):
                assert 8 - 1e-5 <= p.X <= 10 + 1e-5
                assert -15 - 1e-5 <= p.Z <= -5 + 1e-5


@pytest.mark.parametrize("blind", [False, True])
@pytest.mark.parametrize("shift", [0, 0.8])
@pytest.mark.parametrize("sign", [1, -1])
def test_wide_containment_does_not_extend_selected_bore(blind, shift, sign):
    op = operation(blind, sign)
    if shift:
        tool = Tool()
        tool.set_tool_from_segments([
            Segment(Point(edge.start.X, edge.start.Z - shift),
                    Point(edge.end.X, edge.end.Z - shift), edge.bulge)
            for edge in op.tool.get_segmentgroup().getSegments()])
        tool.side = op.tool.side
        op.add_tool(tool)
    op.add_containment(BoundBox(Point(0, -50), Point(sign * 30, 20)))
    op.getGCode()
    assert len(op.tool_paths) == 3
    for group in op.tool_paths:
        points = [point for edge in group.getSegments() for point in (edge.start, edge.end)]
        assert max(point.Z - shift for point in points) == pytest.approx(0, abs=1e-5)
        assert min(point.Z - shift for point in points) >= -20 - 1e-5
        if not blind:
            assert min(point.Z - shift for point in points) == pytest.approx(-20, abs=1e-5)


@pytest.mark.parametrize("shift", [0, 0.6])
def test_wide_containment_does_not_extend_partial_floor_toward_axis(shift):
    op = operation(True)
    op.partSegmentGroup = type(op.partSegmentGroup)()
    op.addPartSegments([Segment(Point(10, 0), Point(10, -20)),
                        Segment(Point(10, -20), Point(5, -20))])
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(edge.start.X - shift, edge.start.Z),
                Point(edge.end.X - shift, edge.end.Z), edge.bulge)
        for edge in op.tool.get_segmentgroup().getSegments()])
    op.add_tool(tool)
    op.add_containment(BoundBox(Point(0, -50), Point(30, 20)))
    op.getGCode()
    for group in op.tool_paths:
        assert group.getSegments()[0].start.X - shift == pytest.approx(5, abs=1e-5)


def test_containment_outside_selected_bore_has_no_cutting_strokes():
    op = operation()
    op.getGCode()
    op.add_containment(BoundBox(Point(0, -50), Point(30, -30)))
    assert [command.to_string() for command in op.getGCode()] == ["G18"]
    assert op.tool_paths == []


def test_failed_generation_does_not_publish_stale_paths():
    op = operation()
    op.getGCode()
    with patch.object(BoreOP, "_clip_path", side_effect=[[], RuntimeError("geometry failure")]):
        with pytest.raises(RuntimeError, match="geometry failure"):
            op.getGCode()
    assert op.tool_paths == []


@pytest.mark.parametrize("name,value", [
    ("finish_passes", -1), ("finish_passes", True), ("finish_passes", 1.5),
    ("pass_offset", 0), ("pass_offset", float("nan")),
    ("stock_to_leave", -1), ("clearance", 0), ("clearance", float("inf"))])
def test_invalid_parameters_leave_no_paths(name, value):
    op = operation()
    op.tool_paths = ["stale"]
    setattr(op, name, value)
    with pytest.raises(ValueError):
        op.getGCode()
    assert op.tool_paths == []


def test_zero_finish_passes_retains_clearing_and_reversed_input_is_rejected():
    op = operation()
    op.finish_passes = 0
    assert any(c.get_movement() == "G1" for c in op.getGCode())
    assert op.clearing_paths and not op.tool_paths
    op.finish_passes = 1
    op.partSegmentGroup = op.partSegmentGroup.reversed()
    with pytest.raises(ValueError, match="mouth toward bottom"):
        op.getGCode()
    assert op.tool_paths == []


@pytest.mark.parametrize("direction", ["X", "Z"])
@pytest.mark.parametrize("blind", [False, True])
@pytest.mark.parametrize("sign", [1, -1])
def test_clearing_direction_and_bottom_to_mouth_finish(direction, blind, sign):
    op = operation(blind, sign)
    op.cut_direction = CutDirection(direction)
    commands = op.getGCode()[1:]
    assert op.clearing_paths
    for group in op.clearing_paths:
        edge = group.getSegments()[0]
        if direction == "X":
            assert edge.start.X == 0
            assert sign * edge.end.X > 0
            assert edge.end.Z == edge.start.Z
        else:
            assert edge.end.Z < edge.start.Z
            assert edge.start.X == edge.end.X
    for group in op.tool_paths:
        edges = group.getSegments()
        assert edges[-1].end.Z > edges[0].start.Z
        assert all(edge.end.Z >= edge.start.Z - 1e-5 for edge in edges)
        if blind:
            assert sign * edges[0].end.X > sign * edges[0].start.X
    first_feed = next(i for i, c in enumerate(commands) if c.get_movement() == "G1")
    expected_x = 0 if direction == "X" else op.clearing_paths[0].getSegments()[0].start.X
    assert commands[first_feed - 1].getParams()["X"] == expected_x
    for previous, current in zip(commands, commands[1:]):
        if current.get_movement() == "G1":
            for command in (previous, current):
                p = command.getParams()
                assert -1e-5 <= sign * p["X"] <= 15 + 1e-5
                assert -20 - 1e-5 <= p["Z"] <= 3 + 1e-5


def test_direction_defaults_to_x_and_invalid_direction_clears_both_path_sets():
    op = operation()
    assert op.getParams()["cut_direction"] is CutDirection.RADIAL
    op.getGCode()
    op.cut_direction = "Y"
    with pytest.raises(ValueError, match="cut_direction"):
        op.getGCode()
    assert not op.tool_paths and not op.clearing_paths


@pytest.mark.parametrize("direction", ["X", "Z"])
def test_wide_radial_limits_do_not_clear_beyond_the_bore(direction):
    op = operation(True)
    op.cut_direction = CutDirection(direction)
    op.add_containment(BoundBox(Point(0, -50), Point(80, 20)))
    op.getGCode()
    assert op.clearing_paths
    for group in op.clearing_paths:
        for edge in group.getSegments():
            assert max(edge.start.X, edge.end.X) < 10
            assert min(edge.start.Z, edge.end.Z) >= -20


@pytest.mark.parametrize("direction", ["X", "Z"])
def test_clearing_reaches_allowance_within_one_increment(direction):
    op = operation(True)
    op.cut_direction = CutDirection(direction)
    op.getGCode()
    allowance = op.stock_to_leave + (op.finish_passes - 1) * op.pass_offset + 0.01
    points = [p for group in op.clearing_paths for edge in group.getSegments()
              for p in (edge.start, edge.end)]
    assert 10 - allowance - op.pass_offset - 0.05 <= max(p.X for p in points) <= 10 - allowance + 0.05
    assert -20 + allowance - 0.05 <= min(p.Z for p in points) <= -20 + allowance + op.pass_offset + 0.05
    stations = sorted({round(p.Z if direction == "X" else p.X, 5)
                       for group in op.clearing_paths for p in (group.getSegments()[0].start,)})
    assert len(stations) > 2
    assert max(b - a for a, b in zip(stations, stations[1:])) <= op.pass_offset + 1e-5


@pytest.mark.parametrize("direction", ["X", "Z"])
def test_nonzero_inner_limit_is_used_for_entry_and_withdrawal(direction):
    op = operation(True)
    op.cut_direction = CutDirection(direction)
    op.add_containment(BoundBox(Point(4, -15), Point(10, -5)))
    moves = op.getGCode()[1:]
    assert moves[0].getParams()["X"] == 4
    assert op.clearing_paths
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() == "G0" and current.getParams()["Z"] > previous.getParams()["Z"]:
            assert current.getParams()["X"] == previous.getParams()["X"]
            if previous.getParams()["Z"] < op.containment.ZMax - 1e-5:
                assert previous.getParams()["X"] == 4
    for group in op.tool_paths:
        assert group.getSegments()[-1].end.Z > group.getSegments()[0].start.Z


@pytest.mark.parametrize("direction", ["X", "Z"])
@pytest.mark.parametrize("sign", [1, -1])
def test_clearing_retract_leaves_cut_perpendicularly(direction, sign):
    op = operation(True, sign)
    op.cut_direction = CutDirection(direction)
    moves = op.getGCode()[1:]
    for group in op.clearing_paths:
        edge = group.getSegments()[-1]
        index = next(i for i, command in enumerate(moves[:-1])
                     if abs(command.getParams()["X"] - edge.end.X) < 1e-5
                     and abs(command.getParams()["Z"] - edge.end.Z) < 1e-5
                     and command.get_movement() == "G1"
                     and abs(moves[i - 1].getParams()["X"] - edge.start.X) < 1e-5
                     and abs(moves[i - 1].getParams()["Z"] - edge.start.Z) < 1e-5)
        following = next(c.getParams() for c in moves[index + 1:]
                         if abs(c.getParams()["X"] - edge.end.X) > 1e-5
                         or abs(c.getParams()["Z"] - edge.end.Z) > 1e-5)
        if direction == "X":
            assert following["X"] == pytest.approx(edge.end.X, abs=1e-5)
            assert following["Z"] > edge.end.Z
        else:
            assert sign * following["X"] < sign * edge.end.X
            assert following["Z"] == pytest.approx(edge.end.Z, abs=1e-5)


def test_radial_disengagement_stays_contained_except_front_boundary_rapid():
    op = operation(True)
    op.add_containment(BoundBox(Point(0, -20), Point(15, 0)))
    moves = op.getGCode()[1:]
    first_end = op.clearing_paths[0].getSegments()[-1].end
    index = next(i for i, c in enumerate(moves)
                 if c.get_movement() == "G1"
                 and c.getParams()["X"] == first_end.X
                 and c.getParams()["Z"] == first_end.Z)
    lift = moves[index + 1]
    assert lift.get_movement() == "G0"
    assert lift.getParams()["X"] == first_end.X
    assert lift.getParams()["Z"] > 0
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() == "G1":
            for command in (previous, current):
                assert -20 - 1e-5 <= command.getParams()["Z"] <= 1e-5


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("partial", [False, True])
def test_z_clearing_positions_x_at_front_clearance_before_axial_feed(sign, partial):
    op = operation(True, sign)
    op.cut_direction = CutDirection.AXIAL
    op.finish_passes = 0
    if partial:
        op.add_containment(BoundBox(Point(sign * 4, -15), Point(sign * 10, -5)))
    moves = op.getGCode()[1:]
    z_clear = op.containment.ZMax + op.clearance
    for group in op.clearing_paths:
        start = group.getSegments()[0].start
        index = next(i for i, c in enumerate(moves)
                     if c.get_movement() == "G1"
                     and abs(c.getParams()["X"] - start.X) < 1e-5
                     and abs(c.getParams()["Z"] - start.Z) < 1e-5)
        assert moves[index - 1].get_movement() == "G0"
        assert moves[index - 1].getParams()["X"] == pytest.approx(start.X)
        assert moves[index - 1].getParams()["Z"] == op.containment.ZMax
        assert moves[index - 2].get_movement() == "G0"
        assert moves[index - 2].getParams()["X"] == pytest.approx(start.X)
        assert moves[index - 2].getParams()["Z"] == z_clear
    for a, b in zip(moves, moves[1:]):
        if sign * b.getParams()["X"] > sign * a.getParams()["X"] + 1e-5:
            assert a.getParams()["Z"] == b.getParams()["Z"] == z_clear
            assert b.get_movement() == "G0"


@pytest.mark.parametrize("sign", [1, -1])
def test_x_clearing_starts_at_inner_containment_boundary(sign):
    op = operation(True, sign)
    op.add_containment(BoundBox(Point(sign * 4, -15), Point(sign * 10, -5)))
    moves = op.getGCode()[1:]
    for group in op.clearing_paths:
        edge = group.getSegments()[0]
        assert edge.start.X == sign * 4
        assert any(a.getParams()["X"] == edge.start.X
                   and abs(a.getParams()["Z"] - edge.start.Z) < 1e-5
                   and b.get_movement() == "G1"
                   and abs(b.getParams()["X"] - edge.end.X) < 1e-5
                   and abs(b.getParams()["Z"] - edge.end.Z) < 1e-5
                   for a, b in zip(moves, moves[1:]))


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("start_depth", [3, 20])
def test_x_clearing_begins_at_containment_start_depth_not_model_mouth(sign, start_depth):
    op = operation(True, sign)
    op.add_containment(BoundBox(Point(0, -20), Point(sign * 15, start_depth)))
    moves = op.getGCode()[1:]
    first = op.clearing_paths[0].getSegments()[0]
    assert first.start.Z == first.end.Z == start_depth
    assert first.start.X == 0
    stations = [g.getSegments()[0].start.Z for g in op.clearing_paths]
    assert stations == sorted(stations, reverse=True)
    assert all(a - b <= op.pass_offset + 1e-5 for a, b in zip(stations, stations[1:]))
    assert any(a.getParams()["X"] == 0 and a.getParams()["Z"] == start_depth
               and b.get_movement() == "G1"
               and b.getParams()["X"] == first.end.X and b.getParams()["Z"] == start_depth
               for a, b in zip(moves, moves[1:]))
    # Extending the clearing region must not extend model finishing geometry.
    for group in op.tool_paths:
        assert max(p.Z for edge in group.getSegments()
                   for p in (edge.start, edge.end)) <= 1e-5


def test_empty_insert_is_rejected_without_stale_paths():
    op = operation()
    op.add_tool(Tool())
    op.tool_paths = ["stale"]
    with pytest.raises(ValueError, match="non-empty insert"):
        op.getGCode()
    assert op.tool_paths == []


@pytest.mark.parametrize("blind", [False, True])
@pytest.mark.parametrize("sign", [1, -1])
def test_every_feed_segment_respects_containment(blind, sign):
    op = operation(blind, sign)
    moves = op.getGCode()[1:]
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() == "G1":
            for command in (previous, current):
                params = command.getParams()
                assert op.containment.XMin - 1e-5 <= params["X"] <= op.containment.XMax + 1e-5
                assert op.containment.ZMin - 1e-5 <= params["Z"] <= op.containment.ZMax + 1e-5


def test_partial_containment_routes_feeds_inside_and_rapids_to_clearance():
    op = operation()
    op.add_containment(BoundBox(Point(8, -15), Point(10, -5)))
    moves = op.getGCode()[1:]
    assert moves[0].getParams()["Z"] == op.containment.ZMax + op.clearance
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() == "G1":
            for command in (previous, current):
                params = command.getParams()
                assert 8 - 1e-5 <= params["X"] <= 10 + 1e-5
                assert -15 - 1e-5 <= params["Z"] <= -5 + 1e-5
