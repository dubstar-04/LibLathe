import math
from unittest.mock import patch

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.debug.plot import Plot
from liblathe.op.base import BaseOP
from liblathe.op.thread import ThreadOP
from liblathe.tool.tool import Tool, ToolSide


def operation(sign=1):
    op = ThreadOP()
    tool = Tool()
    vertices = [(0, 0), (2, -0.5), (2, 0.5), (0, 0)]
    tool.set_tool_from_segments([
        Segment(Point(sign * x, z), Point(sign * u, v))
        for (x, z), (u, v) in zip(vertices, vertices[1:])])
    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
    op.add_tool(tool)
    vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
    op.addPartSegments([
        Segment(Point(sign * x, z), Point(sign * u, v))
        for (x, z), (u, v) in zip(vertices, vertices[1:])])
    op.add_containment(BoundBox(Point(sign * 9.25, -21), Point(sign * 10, 1)))
    op.add_stock(BoundBox(Point(0, -20), Point(sign * 12, 2)))
    op.setParams({"pitch": 1.5, "pass_offset": 0.3, "spring_passes": 2, "clearance": 2})
    return op


def test_g33_pass_depths_pitch_and_spring_passes():
    op = operation()
    commands = op.getGCode()
    assert [command.get_movement() for command in commands[:3]] == ["G18", "G90", "G8"]
    cuts = [command for command in commands if command.get_movement() == "G33"]
    assert [command.getParams()["X"] for command in cuts] == pytest.approx(
        [9.7, 9.4, 9.25, 9.25, 9.25])
    assert all(command.getParams()["Z"] == -21 for command in cuts)
    assert all(command.getParams()["K"] == 1.5 for command in cuts)
    assert all("F" not in command.getParams() for command in cuts)
    assert len(op.tool_paths) == len(cuts)
    for group, command in zip(op.tool_paths, cuts):
        segment = group.getSegments()[0]
        assert segment.start.Z == 1
        assert segment.start.X == segment.end.X == command.getParams()["X"]
        assert segment.end.Z == -21


def test_passes_return_above_the_containment_and_only_enter_and_leave_via_stock_clearance():
    commands = operation().getGCode()[3:]
    lane = 12  # crest 10 + clearance 2
    assert commands[0].getParams() == {"X": 14, "Z": 4.5}
    assert commands[-1].getParams() == commands[0].getParams()
    # collinear radial rapids through the lane are merged at entry and exit
    assert commands[1].getParams() == {"X": 14, "Z": 1}
    assert commands[2].get_movement() == "G0"
    assert commands[2].getParams()["Z"] == 1 and commands[2].getParams()["X"] < lane
    assert commands[-3].get_movement() == "G33"
    assert commands[-2].getParams() == {"X": 14, "Z": -21}
    for previous, command in zip(commands[2:-2], commands[3:-2]):
        start, end = previous.getParams(), command.getParams()
        if command.get_movement() == "G0":
            if start["Z"] != end["Z"]:
                assert start["X"] == end["X"] == lane
            else:
                assert end["Z"] in (1, -21)
                assert lane in (start["X"], end["X"])
        else:
            assert command.get_movement() == "G33"
            assert start["X"] == end["X"]
            assert start["Z"] == 1 and end["Z"] == -21


def test_return_lane_collision_is_reported():
    op = operation()
    op.partSegmentGroup = SegmentGroup()
    vertices = [(0, 0), (10, 0), (10, -8), (13, -8), (13, -12), (10, -12), (10, -20), (0, -20)]
    op.addPartSegments([Segment(Point(*a), Point(*b)) for a, b in zip(vertices, vertices[1:])])
    with pytest.raises(RuntimeError, match="return above the containment"):
        op.getGCode()


def test_near_and_far_commands_and_paths_are_reflected_without_changing_pitch():
    near, far = operation(), operation(-1)
    near_commands, far_commands = near.getGCode(), far.getGCode()
    for first, second in zip(near_commands, far_commands):
        assert first.get_movement() == second.get_movement()
        expected = dict(first.getParams())
        if "X" in expected:
            expected["X"] = -expected["X"]
        assert second.getParams() == expected
    assert far.tool.side is ToolSide.FAR
    assert far.containment.XMax == -9.25
    assert far.partSegmentGroup.boundbox().XMin == -10
    assert all(group.getSegments()[0].start.X < 0 for group in far.tool_paths)
    expected = [command.to_string() for command in far_commands]
    assert [command.to_string() for command in far.getGCode()] == expected
    assert ThreadOP.getGCode is BaseOP.getGCode


@pytest.mark.parametrize("field,value", [
    ("pitch", None), ("pitch", 0), ("pitch", -1), ("pitch", math.nan),
    ("pitch", math.inf), ("pitch", True), ("pitch", "1.5"),
    ("pass_offset", True),
    ("pass_offset", 1e-20), ("clearance", 0), ("clearance", math.inf),
    ("spring_passes", -1), ("spring_passes", 1.5), ("spring_passes", True),
])
def test_invalid_parameters_clear_published_paths(field, value):
    op = operation()
    op.getGCode()
    op.clearing_paths = [op.tool_paths[0]]
    setattr(op, field, value)
    with pytest.raises((ValueError, Warning)):
        op.getGCode()
    assert op.tool_paths == []
    assert op.clearing_paths == []


@pytest.mark.parametrize("limits", [(0, 10, -21, 1), (10, 10, -21, 1)])
def test_external_thread_requires_positive_root_and_nonzero_depth(limits):
    op = operation()
    op.add_containment_from_limits(*limits)
    with pytest.raises(ValueError, match="root and crest"):
        op.getGCode()
    assert not op.tool_paths


def test_entry_without_run_in_is_rejected():
    op = operation()
    op.add_containment_from_limits(9.25, 10, -21, 0)
    with pytest.raises(RuntimeError, match="run-in"):
        op.getGCode()
    assert not op.tool_paths


def shouldered_operation(vertices, sign=1):
    op = operation(sign)
    op.partSegmentGroup = SegmentGroup()
    op.addPartSegments([
        Segment(Point(sign * x, z), Point(sign * u, v), sign * bulge)
        for (x, z, *_), (u, v, bulge) in zip(vertices, vertices[1:])])
    op.add_containment(BoundBox(Point(sign * 9.25, -20), Point(sign * 10, 1)))
    return op


RELIEF = [(0, 0), (9, 0, 0), (10, -1, 0), (10, -20, 0), (8, -20, 0), (8, -23, 0),
          (15, -23, 0), (15, -30, 0), (0, -30, 0)]


@pytest.mark.parametrize("sign", [1, -1])
def test_thread_up_to_a_relief_groove_withdraws_through_its_own_band(sign):
    commands = shouldered_operation(RELIEF, sign).getGCode()
    cuts = [command for command in commands if command.get_movement() == "G33"]
    assert [command.getParams()["X"] for command in cuts] == pytest.approx(
        [sign * x for x in (9.7, 9.4, 9.25, 9.25, 9.25)])
    assert all(command.getParams()["Z"] == -20 for command in cuts)


def test_rounded_thread_start_is_split_at_the_band_edge():
    vertices = [(0, 0), (9, 0, 0), (10, -1, -0.4142136), *RELIEF[3:]]
    assert len(shouldered_operation(vertices).getGCode()) > 4


def test_withdrawal_into_a_shoulder_without_relief_is_rejected():
    vertices = [(0, 0), (10, 0, 0), (10, -20, 0), (15, -20, 0), (15, -30, 0), (0, -30, 0)]
    op = shouldered_operation(vertices)
    with pytest.raises(RuntimeError, match="relief"):
        op.getGCode()
    assert not op.tool_paths


def test_shared_lifecycle_clears_paths_if_emission_fails():
    op = operation()
    with patch.object(op, "generateGCode", side_effect=ValueError("Injected failure")):
        with pytest.raises(ValueError, match="Injected failure"):
            op.getGCode()
    assert op.tool_paths == []
    assert op.clearing_paths == []


def test_g33_backplot_includes_cutting_passes_without_mutating_commands(tmp_path):
    commands = operation().getGCode()
    before = [command.to_string() for command in commands]
    plot = Plot()
    plot.file_location = str(tmp_path) + "/"
    plot.image_name = "thread"
    plot.image_type = ".png"
    plot.set_path_colour("G33", (20, 180, 20))
    with patch.object(plot, "drawline", wraps=plot.drawline) as draw:
        plot.backplot(commands)
    feeds = [call for call in draw.call_args_list if call.args[2] == (20, 180, 20)]
    assert len(feeds) == 5
    assert (tmp_path / "thread.png").is_file()
    assert [command.to_string() for command in commands] == before
