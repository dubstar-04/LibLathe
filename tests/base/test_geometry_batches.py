import math

import pytest

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


def group(vertices):
    return SegmentGroup().fromPoints([Point(*vertex) for vertex in vertices])


def coordinates(source):
    return [(edge.start.X, edge.start.Z, edge.end.X, edge.end.Z, edge.bulge)
            for edge in source.getSegments()]


def test_radial_reflection_preserves_arcs_order_and_source():
    source = SegmentGroup()
    source.addSegment(Segment(Point(2, 3), Point(4, 5), 0.5))
    source.addSegment(Segment(Point(4, 5), Point(6, 8), -0.25))
    before = coordinates(source)
    assert coordinates(source.reflectX()) == [
        (-2, 3, -4, 5, -0.5), (-4, 5, -6, 8, 0.25)]
    assert coordinates(source.reflectX(10)) == [
        (8, 3, 6, 5, -0.5), (6, 5, 4, 8, 0.25)]
    assert coordinates(source.reflectX(10).reflectX(10)) == before
    assert coordinates(source) == before
    assert SegmentGroup().reflectX().count() == 0
    for radius in (math.inf, math.nan):
        with pytest.raises(ValueError, match="finite"):
            source.reflectX(radius)


@pytest.mark.parametrize("curved", [False, True])
def test_batch_sweeps_match_scalar_queries_and_preserve_inputs(curved):
    part = group([(0, 0), (10, 0), (10, -20), (0, -20)])
    tool = group([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
    if curved:
        part = SegmentGroup()
        part.addSegment(Segment(Point(0, 0), Point(10, -10), 0.5))
        part.addSegment(Segment(Point(10, -10), Point(10, -20)))
        part.addSegment(Segment(Point(10, -20), Point(0, -20)))
    originals = coordinates(part), coordinates(tool)
    moves = [(Point(12, 5), Point(12, -15)),
             (Point(12, -15), Point(15, -15)),
             (Point(15, -15), Point(15, 5))]
    for start, end in moves:
        part.validateToolSweep(tool, start, end)
    part.validateToolSweeps(tool, moves)
    colliding = (Point(5, -5), Point(5, -15))
    with pytest.raises(RuntimeError):
        part.validateToolSweep(tool, *colliding)
    with pytest.raises(RuntimeError, match="Tool sweep 3"):
        part.validateToolSweeps(tool, moves + [colliding])
    assert (coordinates(part), coordinates(tool)) == originals


def test_batch_sweeps_empty_queries_and_nonfinite_coordinates():
    SegmentGroup().validateToolSweeps(SegmentGroup(), [])
    part = group([(0, 0), (10, 0), (10, -20), (0, -20)])
    tool = group([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
    with pytest.raises(ValueError, match="finite"):
        part.validateToolSweeps(tool, [(Point(math.nan, 0), Point(15, 0))])
    with pytest.raises(ValueError):
        part.validateToolSweeps(SegmentGroup(), [(Point(15, 0), Point(15, 1))])
    with pytest.raises(ValueError):
        SegmentGroup().validateToolSweeps(tool, [(Point(15, 0), Point(15, 1))])


def test_batch_sweeps_use_fresh_geometry_on_each_call():
    part = group([(0, 0), (10, 0), (10, -20), (0, -20)])
    tool = group([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
    moves = [(Point(11, -10), Point(11, -15))]
    part.validateToolSweeps(tool, moves)
    tool.addSegment(Segment(Point(-2, 0), Point(-2, 2)))
    with pytest.raises(RuntimeError):
        part.validateToolSweeps(tool, moves)
