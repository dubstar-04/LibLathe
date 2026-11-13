import math
from unittest.mock import patch

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segmentgroup import StockPreview
from liblathe.op.drill import DrillOP
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
