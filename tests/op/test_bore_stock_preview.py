import pytest

from liblathe.base.segmentgroup import StockPreview
from liblathe.op.base import CutDirection
from tests.op.test_bore_op import geometry, operation


def contains(snapshot, x, z):
    return any(all((b[0] - a[0]) * (z - a[1]) - (b[1] - a[1]) * (x - a[0]) >= -1e-8
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]))
               for polygon in snapshot.polygons())


@pytest.mark.parametrize("direction", list(CutDirection))
@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("blind", [False, True])
def test_generated_bore_stock_uses_unmodified_shared_sweep_core(direction, sign, blind):
    op = operation(blind, sign)
    op.cut_direction = direction
    commands = op.getGCode()
    paths = geometry(op)
    tool = [(sign * edge.start.X, edge.start.Z)
            for edge in op.tool.get_segmentgroup().getSegments()]
    moves = []
    previous = None
    for command in commands:
        params = command.getParams()
        if "X" not in params:
            continue
        current = (sign * params["X"], params["Z"])
        if previous is not None and command.get_movement() == "G1":
            moves.append((*previous, *current))
        previous = current
    before = StockPreview([(0, -25), (20, -25), (20, 0), (0, 0)])
    after = before.copy()
    after.remove_feeds(tool, moves)
    assert before.area == 500
    assert 0 < after.area < before.area
    assert not contains(after, 5, -10)
    assert contains(after, 15, -10)
    assert contains(after, 5, -23)
    if blind:
        assert contains(after, 5, -19.9)  # Floor allowance retained.
    else:
        assert not contains(after, 5, -19.9)
    assert contains(before, 5, -10)
    edges = after.edges()
    assert sum((x0 * z1 - x1 * z0) / 2 for x0, z0, x1, z1 in edges) == pytest.approx(after.area)
    # Preview is downstream-only; it must not change planning or source paths.
    assert geometry(op) == paths
    assert [c.to_string() for c in op.getGCode()] == [c.to_string() for c in commands]
