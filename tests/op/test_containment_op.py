from unittest.mock import Mock

import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.op.bore import BoreOP
from liblathe.op.face import FaceOP
from liblathe.op.groove import GrooveOP
from liblathe.op.partoff import PartoffOP
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP
from liblathe.tool.tool import Tool, ToolSide


@pytest.mark.parametrize("axial_shift", [-2, 0, 2])
@pytest.mark.parametrize("operation_type", [ProfileOP, RoughOP, GrooveOP])
def test_defeature_scan_covers_reference_depth(operation_type, axial_shift):
    operation = operation_type()
    operation.add_containment(BoundBox(Point(0, -15), Point(15, 5)))
    vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
    operation.addPartSegments([Segment(Point(*a), Point(*b))
                               for a, b in zip(vertices, vertices[1:])])
    vertices = [(0, -2), (0, 0), (2, 0), (2, -2), (0, -2)]
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(a[0], a[1] + axial_shift), Point(b[0], b[1] + axial_shift))
        for a, b in zip(vertices, vertices[1:])])
    operation.add_tool(tool)
    original = operation.partSegmentGroup
    contours = []

    def observe(bounds, insert, allow_grooving):
        result = original.defeature(bounds, insert, allow_grooving)
        contours.append(result)
        return result

    operation.partSegmentGroup = Mock(wraps=original)
    operation.partSegmentGroup.defeature.side_effect = observe
    operation.generatePath()
    assert len(contours) == 1
    required_depth = min(-15, -15 - tool.get_segmentgroup().boundbox().ZMin)
    assert contours[0].boundbox().ZMin <= required_depth
    assert operation.tool_paths
    if operation_type is ProfileOP:
        assert min(group.boundbox().ZMin for group in operation.tool_paths) == pytest.approx(-15)
    assert operation.containment.ZMin == -15
    assert operation.containment.ZMax == 5


def test_roughing_reaches_taper_below_old_scan_endpoint():
    operation = RoughOP()
    operation.setParams({"pass_offset": 0.25, "allow_grooving": True})
    operation.add_containment(BoundBox(Point(0, -15), Point(15, 5)))
    vertices = [(0, 0), (10, 0), (10, -10), (6, -20), (0, -20)]
    operation.addPartSegments([Segment(Point(*a), Point(*b))
                               for a, b in zip(vertices, vertices[1:])])
    vertices = [(0, -2), (0, 0), (2, 0), (2, -2), (0, -2)]
    tool = Tool()
    tool.set_tool_from_segments([Segment(Point(*a), Point(*b))
                                 for a, b in zip(vertices, vertices[1:])])
    operation.add_tool(tool)
    operation.generatePath()
    assert any(abs(segment.start.X - 8.25) < 1e-5
               and abs(segment.end.X - 8.25) < 1e-5
               and segment.start.Z < -14
               and abs(segment.end.Z + 15) < 1e-5
               for group in operation.tool_paths for segment in group.getSegments())


@pytest.mark.parametrize("operation_type", [FaceOP, RoughOP, ProfileOP, GrooveOP, PartoffOP, BoreOP])
@pytest.mark.parametrize("sign", [1, -1])
def test_every_operation_contains_all_feeds(operation_type, sign):
    operation = operation_type()
    operation.setParams({"pass_offset": 1, "finish_passes": 2, "clearance": 1})
    if operation_type is GrooveOP:
        operation.setParams({"finish_pass_offset": 0.1})
    operation.add_containment(BoundBox(Point(0, -25), Point(sign * 15, 3)))
    operation.add_stock(BoundBox(Point(0, -25), Point(sign * 12, 1)))
    vertices = [(10, 0), (10, -20)] if operation_type is BoreOP else [
        (0, 0), (10, 0), (10, -20), (0, -20)]
    operation.addPartSegments([Segment(Point(sign * x, z), Point(sign * u, v))
                               for (x, z), (u, v) in zip(vertices, vertices[1:])])
    vertices = [(-0.4, -0.4), (-0.4, 2), (2, 2), (2, -0.4), (-0.4, -0.4)]
    tool = Tool()
    tool.set_tool_from_segments([Segment(Point(sign * x, z), Point(sign * u, v))
                                 for (x, z), (u, v) in zip(vertices, vertices[1:])])
    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
    operation.add_tool(tool)
    moves = [c for c in operation.getGCode() if c.get_movement() in ("G0", "G1", "G2", "G3")]
    assert any(c.get_movement() == "G1" for c in moves)
    for previous, current in zip(moves, moves[1:]):
        if current.get_movement() in ("G1", "G2", "G3"):
            for command in (previous, current):
                position = command.getParams()
                assert -1e-5 <= sign * position["X"] <= 15 + 1e-5
                assert -25 - 1e-5 <= position["Z"] <= 3 + 1e-5
    if operation_type is PartoffOP:
        cuts = operation.tool_paths[0].getSegments()
        assert cuts[0].start.Z == -25
        assert cuts[-1].end.X == 0
        cut_end = next(i for i, c in enumerate(moves)
                       if c.get_movement() == "G1"
                       and abs(c.getParams()["X"]) < 1e-5
                       and abs(c.getParams()["Z"] + 25) < 1e-5)
        withdrawal = moves[cut_end + 1]
        assert withdrawal.get_movement() == "G1"
        assert withdrawal.getParams()["Z"] == pytest.approx(-25)
        assert sign * withdrawal.getParams()["X"] == pytest.approx(15)
        for previous, current in zip(moves[cut_end:], moves[cut_end + 1:]):
            if abs(current.getParams()["Z"] - previous.getParams()["Z"]) > 1e-5:
                assert current.get_movement() == "G0"
                assert sign * previous.getParams()["X"] > 12
                assert sign * current.getParams()["X"] > 12
