import math
from unittest.mock import patch

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segmentgroup import StockPreview
from liblathe.op.drill import DrillOP, RetractMode
from liblathe.op.base import BaseOP
from liblathe.tool.drill import Drill
from liblathe.tool.tool import Tool, ToolSide


def operation():
    op = DrillOP()
    op.add_tool(Drill(10, 118, 50))
    op.add_containment_from_limits(0, 5, -20, 0)
    op.add_stock(BoundBox(Point(0, -30), Point(20, 0)))
    op.vfeed = 60
    op.clearance = 3
    return op


def test_straight_tip_depth_path_and_clearance():
    op = operation()
    commands = op.getGCode()
    assert [c.get_movement() for c in commands] == ["G0", "G0", "G1", "G0"]
    assert [c.getParams() for c in commands] == [
        {"X": 0, "Z": 3}, {"X": 0, "Z": 0},
        {"X": 0, "Z": -20, "F": 60}, {"X": 0, "Z": 3}]
    edge = op.tool_paths[0].getSegments()[0]
    assert edge.start.isSame(Point(0, 0))
    assert edge.end.isSame(Point(0, -20))
    assert op.tool.point_length == pytest.approx(5 / math.tan(math.radians(59)))


def test_full_retract_pecks_preserve_clearance_and_reentry_gap():
    op = operation()
    op.setParams({"peck_depth": 7, "reentry_gap_diameters": 0.1})
    commands = op.getGCode()
    assert [(c.get_movement(), c.getParams()["Z"]) for c in commands] == [
        ("G0", 3), ("G0", 0), ("G1", -7), ("G0", 3),
        ("G0", -6), ("G1", -14), ("G0", 3),
        ("G0", -13), ("G1", -20), ("G0", 3),
    ]
    assert all(c.getParams()["X"] == 0 for c in commands)
    assert all(c.getParams()["F"] == 60 for c in commands if c.get_movement() == "G1")
    assert [(g.getSegments()[0].start.Z, g.getSegments()[0].end.Z) for g in op.tool_paths] == [
        (0, -7), (-6, -14), (-13, -20)]


def test_partial_retract_pecks_without_returning_to_front():
    op = operation()
    op.setParams({"peck_depth": 7, "retract_mode": RetractMode.PARTIAL_RETRACT,
                  "chip_break_retract_diameters": 0.1})
    assert [(c.get_movement(), c.getParams()["Z"]) for c in op.getGCode()] == [
        ("G0", 3), ("G0", 0), ("G1", -7), ("G0", -6),
        ("G1", -14), ("G0", -13), ("G1", -20), ("G0", 3),
    ]


def test_small_partial_retracts_survive_rapid_optimisation():
    op = operation()
    op.setParams({"peck_depth": 7, "retract_mode": RetractMode.PARTIAL_RETRACT,
                  "chip_break_retract_diameters": 5e-8})
    commands = op.getGCode()
    starts = [group.getSegments()[0].start.Z for group in op.tool_paths]
    assert 0 < starts[1] - (-7) < 1e-6
    assert 0 < starts[2] - (-14) < 1e-6
    assert [(c.get_movement(), c.getParams()["Z"]) for c in commands] == [
        ("G0", 3), ("G0", 0), ("G1", -7), ("G0", starts[1]),
        ("G1", -14), ("G0", starts[2]), ("G1", -20), ("G0", 3),
    ]


@pytest.mark.parametrize("mode", list(RetractMode))
def test_default_diameter_gap_is_capped_at_start_depth(mode):
    op = operation()
    op.setParams({"peck_depth": 7, "retract_mode": mode})
    commands = op.getGCode()
    feeds = [c.getParams()["Z"] for c in commands if c.get_movement() == "G1"]
    assert feeds == [-7, -14, -20]
    starts = [g.getSegments()[0].start.Z for g in op.tool_paths]
    assert starts == [0, 0, -4]


@pytest.mark.parametrize("mode", list(RetractMode))
def test_peck_larger_than_hole_depth_matches_straight_drill(mode):
    op = operation()
    original = [c.to_string() for c in op.getGCode()]
    op.setParams({"peck_depth": 25, "retract_mode": mode})
    assert [c.to_string() for c in op.getGCode()] == original


@pytest.mark.parametrize("peck_depth", [0, 7])
def test_tip_compensation_reaches_full_diameter_at_final_depth(peck_depth):
    op = operation()
    op.setParams({"tip_compensation": True, "peck_depth": peck_depth})
    commands = op.getGCode()
    final = min(c.getParams()["Z"] for c in commands)
    assert final + op.tool.point_length == pytest.approx(op.containment.ZMin, abs=1e-5)
    assert op.tool_paths[-1].getSegments()[0].end.Z == final
    assert commands[-1].getParams()["Z"] == 3


def test_tip_compensation_checks_the_extended_tool_reach():
    op = operation()
    op.add_containment_from_limits(0, 5, -49, 0)
    op.getGCode()
    op.tip_compensation = True
    with pytest.raises(ValueError, match="tool length"):
        op.getGCode()
    assert op.tool_paths == []


def test_tip_compensation_lost_at_coordinate_precision_is_rejected():
    op = operation()
    op.add_containment_from_limits(0, 5, 99999984, 100000000)
    op.tip_compensation = True
    with pytest.raises(ValueError, match="drill-tip compensation at coordinate precision"):
        op.getGCode()
    assert op.tool_paths == []


def test_tip_compensation_checks_reach_after_coordinate_rounding():
    op = operation()
    op.add_tool(Drill(14, 118, 22))
    op.add_containment_from_limits(0, 7, 99999984, 100000000)
    op.tip_compensation = True
    with pytest.raises(ValueError, match="tool length"):
        op.getGCode()
    assert op.tool_paths == []


@pytest.mark.parametrize("params", [
    {"peck_depth": -1}, {"peck_depth": math.nan}, {"peck_depth": math.inf},
    {"peck_depth": 7, "retract_mode": "Full Retract"},
    {"peck_depth": 7, "reentry_gap_diameters": 0},
    {"peck_depth": 7, "reentry_gap_diameters": math.inf},
    {"peck_depth": 7, "retract_mode": RetractMode.PARTIAL_RETRACT,
     "chip_break_retract_diameters": -1},
    {"peck_depth": 7, "retract_mode": RetractMode.PARTIAL_RETRACT,
     "chip_break_retract_diameters": math.nan},
])
def test_invalid_peck_settings_clear_previous_paths(params):
    op = operation()
    op.getGCode()
    op.setParams(params)
    with pytest.raises(ValueError):
        op.getGCode()
    assert op.tool_paths == []


def test_excessive_peck_count_is_rejected():
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 100)
    op.peck_depth = 1e-10
    with pytest.raises(ValueError, match="pecks"):
        op.getGCode()
    assert op.tool_paths == []


def test_partial_retract_lost_at_coordinate_precision_is_rejected():
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 100)
    op.setParams({"peck_depth": 7, "retract_mode": RetractMode.PARTIAL_RETRACT,
                  "chip_break_retract_diameters": 1e-10})
    with pytest.raises(ValueError, match="retract at coordinate precision"):
        op.getGCode()
    assert op.tool_paths == []


def test_translated_pecks_finish_an_exact_multiple_without_an_extra_peck():
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 100)
    op.peck_depth = 5
    feeds = [c.getParams()["Z"] for c in op.getGCode() if c.get_movement() == "G1"]
    assert feeds == [95, 90, 85, 80]


@pytest.mark.parametrize("peck_depth,expected_count", [(20 / 3, 3), (0.002, 10000)])
def test_translated_pecks_do_not_accumulate_coordinate_rounding(peck_depth, expected_count):
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 100)
    op.peck_depth = peck_depth
    feeds = [c.getParams()["Z"] for c in op.getGCode() if c.get_movement() == "G1"]
    assert len(feeds) == expected_count
    assert feeds[-1] == 80
    assert all(previous > current for previous, current in zip(feeds, feeds[1:]))


def test_shared_lifecycle_retains_centreline_dispatch():
    assert DrillOP.getGCode is BaseOP.getGCode
    op = operation()
    expected = [command.to_string() for command in op.getGCode()]
    op.tool.side = ToolSide.FAR
    assert [command.to_string() for command in op.getGCode()] == expected


@pytest.mark.parametrize("error", [ValueError, RuntimeError])
def test_shared_lifecycle_clears_both_path_sets_on_emission_failure(error):
    op = operation()

    def fail():
        op.clearing_paths = [op.tool_paths[0]]
        raise error("Injected emission failure")

    with patch.object(op, "generateGCode", side_effect=fail):
        with pytest.raises(error, match="Injected emission failure"):
            op.getGCode()
    assert op.tool_paths == []
    assert op.clearing_paths == []


@pytest.mark.parametrize("diameter,angle,length", [
    (0, 118, 50), (-1, 118, 50), (10, 0, 50), (10, 180, 50),
    (10, 118, 0), (10, 118, 1), (math.nan, 118, 50),
    (10, math.inf, 50), (10, 118, math.inf)])
def test_invalid_drill(diameter, angle, length):
    with pytest.raises(ValueError):
        Drill(diameter, angle, length)


@pytest.mark.parametrize("field,value", [
    ("clearance", 0), ("clearance", math.inf), ("tool", Tool()), ("tool", None),
    ("containment", None)])
def test_invalid_operation_clears_previous_paths(field, value):
    op = operation()
    op.getGCode()
    setattr(op, field, value)
    with pytest.raises(ValueError):
        op.getGCode()
    assert op.tool_paths == []


@pytest.mark.parametrize("limits", [(1, 5, -20, 0), (0, 5, -60, 0)])
def test_excluded_axis_and_excess_reach(limits):
    op = operation()
    op.add_containment_from_limits(*limits)
    with pytest.raises(ValueError):
        op.getGCode()
    assert not op.tool_paths


def test_rotated_drill_rejected():
    op = operation()
    op.tool.tool_rotation = 10
    with pytest.raises(ValueError, match="unrotated"):
        op.getGCode()
    assert not op.tool_paths


def test_missing_clearance_reports_front_clearance():
    op = operation()
    op.clearance = 0
    with pytest.raises(ValueError, match="front clearance"):
        op.getGCode()
    assert not op.tool_paths


def test_clearance_lost_at_start_depth_precision_is_rejected():
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 100)
    op.clearance = 1e-20
    with pytest.raises(ValueError, match="coordinate precision"):
        op.getGCode()
    assert not op.tool_paths


@pytest.mark.parametrize("feed", [0, -1, 75])
def test_feed_passed_through_like_other_turning_operations(feed):
    op = operation()
    op.vfeed = feed
    assert op.getGCode()[2].getParams()["F"] == feed


def test_translated_depths_and_start_ahead_of_stock():
    op = operation()
    op.add_containment_from_limits(0, 5, 80, 105)
    op.add_stock(BoundBox(Point(0, 70), Point(20, 100)))
    commands = op.getGCode()
    assert [c.getParams()["Z"] for c in commands] == [108, 105, 80, 108]


def test_reported_start_106_ahead_of_stock_100():
    op = operation()
    op.add_containment_from_limits(0, 5, 85, 106)
    op.add_stock(BoundBox(Point(0, 0), Point(20, 100)))
    assert [c.getParams()["Z"] for c in op.getGCode()] == [109, 106, 85, 109]


@pytest.mark.parametrize("start,stock_front", [(99, 100), (105, 110)])
def test_user_defined_start_inside_original_stock_is_preserved(start, stock_front):
    op = operation()
    op.add_containment_from_limits(0, 5, 85, start)
    op.add_stock(BoundBox(Point(0, 0), Point(20, stock_front)))
    assert [c.getParams()["Z"] for c in op.getGCode()] == [start + 3, start, 85, start + 3]


@pytest.mark.parametrize("final", [-20, -35])
def test_shared_stock_preview_preserves_drill_point_and_supports_breakthrough(final):
    op = operation()
    op.add_containment_from_limits(0, 5, final, 0)
    commands = [c.to_string() for c in op.getGCode()]
    tool = [(edge.start.X, edge.start.Z) for edge in op.tool.get_segmentgroup().getSegments()]
    before = StockPreview([(0, -30), (20, -30), (20, 0), (0, 0)])
    after = before.copy()
    after.remove_feeds(tool, [(0, 0, 0, final)])
    removed = 5 * min(-final, 30)
    if final > -30:
        removed -= 5 * op.tool.point_length / 2
    assert before.area - after.area == pytest.approx(removed)
    assert before.area == 600
    assert [c.to_string() for c in op.getGCode()] == commands
