import math
from unittest.mock import patch

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.op.base import BaseOP
from liblathe.op.bore import BoreOP
from liblathe.op.drill import DrillOP
from liblathe.op.face import FaceOP
from liblathe.op.groove import GrooveOP
from liblathe.op.partoff import PartoffOP
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP
from liblathe.op.thread import ThreadOP
from liblathe.tool.tool import Tool, ToolSide
from tests.op.test_bore_op import operation as bore
from tests.op.test_drill_op import operation as drill
from tests.op.test_thread_op import operation as thread


OPERATIONS = (FaceOP, RoughOP, ProfileOP, GrooveOP, PartoffOP, BoreOP, DrillOP, ThreadOP)


def operation(operation_type, sign=1):
    if operation_type is DrillOP:
        return drill()
    if operation_type is BoreOP:
        return bore(sign=sign)
    if operation_type is ThreadOP:
        return thread(sign=sign)
    op = operation_type()
    op.pass_offset = 1
    op.finish_passes = 2
    op.clearance = 1
    op.add_containment(BoundBox(Point(0, -15), Point(sign * 15, 5)))
    op.add_stock(BoundBox(Point(0, -25), Point(sign * 12, 1)))
    vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
    op.addPartSegments([Segment(Point(sign * x, z), Point(sign * u, v))
                        for (x, z), (u, v) in zip(vertices, vertices[1:])])
    vertices = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    tool = Tool()
    tool.set_tool_from_segments([Segment(Point(sign * x, z), Point(sign * u, v))
                                 for (x, z), (u, v) in zip(vertices, vertices[1:])])
    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
    op.add_tool(tool)
    return op


@pytest.mark.parametrize("operation_type", OPERATIONS)
@pytest.mark.parametrize("method", ["generatePath", "getGCode"])
@pytest.mark.parametrize("field,value", [
    ("tool", None), ("containment", None), ("clearance", math.nan),
    ("containment", BoundBox(Point(0, -20), Point(math.inf, 3))),
])
def test_invalid_inputs_clear_both_path_sets(operation_type, method, field, value):
    op = operation(operation_type)
    op.tool_paths = [object()]
    op.clearing_paths = [object()]
    setattr(op, field, value)
    with pytest.raises((ValueError, Warning)):
        getattr(op, method)()
    assert op.tool_paths == []
    assert op.clearing_paths == []


@pytest.mark.parametrize("operation_type", [FaceOP, RoughOP, ProfileOP, GrooveOP, BoreOP, ThreadOP])
@pytest.mark.parametrize("step", [0, -1, math.nan, math.inf])
def test_used_increments_are_validated_before_geometry(operation_type, step):
    op = operation(operation_type)
    op.pass_offset = step
    op.tool_paths = [object()]
    op.clearing_paths = [object()]
    with patch.object(op, "_defeature_profile", side_effect=AssertionError("Geometry reached")):
        with pytest.raises(ValueError, match="pass_offset"):
            op.generatePath()
    assert op.tool_paths == []
    assert op.clearing_paths == []


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("operation_type", OPERATIONS)
def test_generation_replaces_paths_and_preserves_commands(operation_type, sign):
    op = operation(operation_type, sign)
    expected = [command.to_string() for command in op.getGCode()]
    counts = len(op.tool_paths), len(op.clearing_paths)
    assert sum(counts) > 0
    assert [command.to_string() for command in op.getGCode()] == expected
    assert (len(op.tool_paths), len(op.clearing_paths)) == counts


@pytest.mark.parametrize("method", ["generatePath", "getGCode"])
def test_facing_clipping_failure_publishes_no_partial_paths(method):
    op = operation(FaceOP)
    original = op._clip_path
    count = 0

    def clip(group):
        nonlocal count
        count += 1
        if count == 2:
            raise ValueError("Injected clipping failure")
        return original(group)

    with patch.object(op, "_clip_path", side_effect=clip):
        with pytest.raises(ValueError, match="Injected clipping failure"):
            getattr(op, method)()
    assert count == 2
    assert op.tool_paths == []
    assert op.clearing_paths == []


def test_fixed_increment_stations_preserve_grid():
    assert list(BaseOP._stations(0, 1, 0.25)) == [0, 0.25, 0.5, 0.75]
    assert list(BaseOP._stations(0, 1, 0.25, include_end=True)) == [0, 0.25, 0.5, 0.75, 1]
    assert list(BaseOP._stations(1e20, 1e20, 1, include_end=True)) == [1e20]


@pytest.mark.parametrize("low,high,step", [(1e20, 2e20, 1), (1e8, 2e8, 0.25)])
def test_fixed_increment_stations_reject_nonprogress(low, high, step):
    stations = BaseOP._stations(low, high, step)
    assert next(stations) == low
    with pytest.raises(ValueError, match="coordinate precision"):
        next(stations)


def test_parameters_cannot_replace_methods_or_publish_partial_updates():
    op = BaseOP()
    previous = op.pass_offset
    with pytest.raises(Warning, match="undefined parameter"):
        op.setParams({"pass_offset": 0.5, "generatePath": 123})
    assert callable(op.generatePath)
    assert op.pass_offset == previous
    op.setParams({"leadin_angle": 0.2, "leadout_angle": 0.3})
    assert op.leadin_angle == 0.2
    assert op.leadout_angle == 0.3
