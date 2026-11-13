import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import StockPreview
from liblathe.op.base import Direction, MachiningMode
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP
from liblathe.tool.tool import Tool, ToolSide


def _contains(snapshot, x, z):
    return any(all((b[0] - a[0]) * (z - a[1]) - (b[1] - a[1]) * (x - a[0]) >= -1e-8
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]))
               for polygon in snapshot.polygons())


@pytest.mark.parametrize(
    ("operation_type", "direction"),
    ((ProfileOP, Direction.RADIAL), (RoughOP, Direction.NEGATIVE_Z)),
)
@pytest.mark.parametrize(("sign", "side"), ((1, ToolSide.NEAR), (-1, ToolSide.FAR)))
def test_internal_frame_routes_from_the_axis_side(operation_type, direction, sign, side):
    operation = operation_type()
    operation.setParams({"mode": MachiningMode.INTERNAL, "direction": direction,
                         "pass_offset": 0.5, "finish_passes": 3, "stock_to_leave": 0.2})
    operation.addPartSegments([Segment(Point(sign * 10, 0), Point(sign * 10, -20))])
    operation.add_containment(BoundBox(Point(0, -20), Point(sign * 15, 3)))
    operation.add_stock(BoundBox(Point(0, -25), Point(sign * 20, 5)))

    vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(sign * x1, z1), Point(sign * x2, z2))
        for (x1, z1), (x2, z2) in zip(vertices, vertices[1:])
    ])
    tool.side = side
    operation.add_tool(tool)

    commands = operation.getGCode()
    radial_coordinates = [command.getParams()["X"] for command in commands
                          if "X" in command.getParams()]
    assert operation.tool_paths
    assert commands
    if side == ToolSide.NEAR:
        assert min(radial_coordinates) >= -1e-5
    else:
        assert max(radial_coordinates) <= 1e-5


# Rhombic boring insert with nose radii, as exported from a FreeCAD tool bit.
_BORING_TOOL = [
    (-0.4985, 4.0105, -0.3167, 3.8287, 0.3640),
    (-0.3167, 3.8287, -0.0008, 0.2174, 0.0000),
    (-0.0008, 0.2174, -0.2174, 0.0008, 0.4663),
    (-0.2174, 0.0008, -3.8287, 0.3167, 0.0000),
    (-3.8287, 0.3167, -4.0105, 0.4985, 0.3640),
    (-4.0105, 0.4985, -4.3265, 4.1098, 0.0000),
    (-4.3265, 4.1098, -4.1098, 4.3265, 0.4663),
    (-4.1098, 4.3265, -0.4985, 4.0105, 0.0000),
]


def _blind_bore_profile(direction):
    operation = ProfileOP()
    operation.setParams({"mode": MachiningMode.INTERNAL, "direction": direction,
                         "pass_offset": 1.0, "finish_passes": 5, "stock_to_leave": 0.0,
                         "clearance": 3.0})
    operation.addPartSegments([Segment(Point(15, 100), Point(15, 75)),
                               Segment(Point(15, 75), Point(0, 75))])
    operation.add_containment(BoundBox(Point(0, 75), Point(15, 102)))
    operation.add_stock(BoundBox(Point(0, 0), Point(50, 110)))
    tool = Tool()
    tool.set_tool_from_segments([
        Segment(Point(x1, z1), Point(x2, z2), bulge) for x1, z1, x2, z2, bulge in _BORING_TOOL
    ])
    operation.add_tool(tool)
    operation.getGCode()
    return operation


def test_internal_radial_profile_retraces_the_axial_pass_out_through_the_mouth():
    radial = _blind_bore_profile(Direction.RADIAL)
    axial = _blind_bore_profile(Direction.NEGATIVE_Z)

    mouth = radial.partSegmentGroup.boundbox().ZMax
    assert len(radial.tool_paths) == radial.finish_passes
    for radial_pass, axial_pass in zip(radial.tool_paths, axial.tool_paths):
        expected = [value for s in axial_pass.reversed().getSegments()
                    for value in (s.start.X, s.start.Z, s.end.X, s.end.Z)]
        actual = [value for s in radial_pass.getSegments()
                  for value in (s.start.X, s.start.Z, s.end.X, s.end.Z)]
        assert actual == pytest.approx(expected)
        segments = radial_pass.getSegments()
        assert segments[0].start.X == pytest.approx(radial.containment.XMin, abs=0.02)
        assert segments[-1].end.Z > mouth


def test_internal_radial_roughing_clears_from_axis_toward_bore_wall():
    operation = RoughOP()
    operation.setParams({"mode": MachiningMode.INTERNAL, "direction": Direction.RADIAL,
                         "allow_grooving": True, "pass_offset": 0.5})
    operation.addPartSegments([Segment(Point(10, 0), Point(10, -20))])
    operation.add_containment(BoundBox(Point(0, -20), Point(15, 3)))
    tool = Tool()
    vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
    tool.set_tool_from_segments([
        Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])
    ])
    operation.add_tool(tool)

    commands = operation.getGCode()
    deep_layers = [group.boundbox() for group in operation.tool_paths
                   if group.boundbox().ZMin < -1]

    assert commands
    assert deep_layers
    assert min(bounds.XMin for bounds in deep_layers) == pytest.approx(0, abs=1e-5)
    assert max(bounds.XMax for bounds in deep_layers) == pytest.approx(10, abs=0.05)


def test_internal_roughing_stock_preview_uses_physical_path_coordinates():
    operation = RoughOP()
    operation.setParams({"mode": MachiningMode.INTERNAL, "direction": Direction.RADIAL,
                         "allow_grooving": True, "pass_offset": 0.5})
    operation.addPartSegments([Segment(Point(10, 0), Point(10, -20))])
    operation.add_containment(BoundBox(Point(0, -20), Point(15, 3)))
    operation.add_stock(BoundBox(Point(0, -25), Point(20, 5)))
    tool = Tool()
    vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
    tool.set_tool_from_segments([
        Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])
    ])
    operation.add_tool(tool)

    commands = operation.getGCode()
    paths = [[(segment.start.X, segment.start.Z, segment.end.X, segment.end.Z, segment.bulge)
              for segment in group.getSegments()] for group in operation.tool_paths]
    tool_profile = [(segment.start.X, segment.start.Z)
                    for segment in operation.tool.get_segmentgroup().getSegments()]
    moves = []
    previous = None
    for command in commands:
        params = command.getParams()
        if "X" not in params:
            continue
        current = (params["X"], params["Z"])
        if previous is not None and command.get_movement() == "G1":
            moves.append((*previous, *current))
        previous = current

    before = StockPreview([(0, -25), (20, -25), (20, 0), (0, 0)])
    after = before.copy()
    after.remove_feeds(tool_profile, moves)

    assert before.area == 500
    assert 0 < after.area < before.area
    assert not _contains(after, 5, -10)
    assert _contains(after, 15, -10)
    assert _contains(after, 5, -23)
    assert paths == [[(segment.start.X, segment.start.Z, segment.end.X, segment.end.Z, segment.bulge)
                      for segment in group.getSegments()] for group in operation.tool_paths]
    assert [command.to_string() for command in operation.getGCode()] == [
        command.to_string() for command in commands]
