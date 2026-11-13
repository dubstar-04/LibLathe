import pytest

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.op.reachable_profile import ReachableProfile


def test_offset_samples_dilates_a_flat_profile_radially():
    samples = [Point(10, 0), Point(10, -1), Point(10, -2)]

    offset = ReachableProfile(samples).offset(0.5)

    assert offset.value_at(0) == pytest.approx(10.5)
    assert offset.value_at(-1) == pytest.approx(10.5)
    assert offset.samples[0].Z == pytest.approx(0.5)
    assert offset.samples[-1].Z == pytest.approx(-2.5)


def test_offset_samples_tracks_native_offset_within_profile_tolerance():
    part = SegmentGroup()
    vertices = [(0, 0), (10, 0), (10, -5), (6, -5),
                (6, -11), (10, -11), (10, -18), (0, -18)]
    for start, end in zip(vertices, vertices[1:] + vertices[:1]):
        part.addSegment(Segment(Point(*start), Point(*end)))
    tool = SegmentGroup()
    vertices = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    for start, end in zip(vertices, vertices[1:]):
        tool.addSegment(Segment(Point(*start), Point(*end)))

    result = part.defeatureWithSamples(BoundBox(Point(0, 1), Point(12, -18)), tool, True)
    distance = 0.2
    offset = ReachableProfile(result.samples).offset(distance)
    native = result.contour.offset(distance)
    native_bounds = native.boundbox()
    x_start, x_end = native_bounds.XMax + 1, native_bounds.XMin - 1
    errors = []
    for sample in result.samples[::15]:
        query = Segment(Point(x_start, sample.Z), Point(x_end, sample.Z))
        intersections = [
            point.X
            for edge in native.getSegments()
            for point in edge.intersect(query)
        ]
        if intersections:
            errors.append(abs(offset.value_at(sample.Z) - max(intersections)))
    assert len(errors) > 100
    assert max(errors) <= SegmentGroup.offsetTolerance + SegmentGroup.defeatureResolution


def test_intervals_below_finds_disjoint_groove_regions():
    samples = [
        Point(15, 0),
        Point(10, -1),
        Point(10, -2),
        Point(10, -3),
        Point(15, -4),
        Point(10, -5),
        Point(10, -6),
        Point(10, -7),
        Point(15, -8),
    ]

    intervals = ReachableProfile(samples).intervals_below(12)

    for actual, expected in zip(intervals, [(-1.6, -2.4), (-5.6, -6.4)]):
        assert actual == pytest.approx(expected)


def test_intervals_between_excludes_regions_already_below_the_layer():
    profile = ReachableProfile([
        Point(15, 0), Point(15, -1), Point(10, -2), Point(10, -3),
        Point(10, -4), Point(15, -5), Point(15, -6),
    ])

    intervals = profile.intervals_between(12, 16)

    assert len(intervals) == 2
    assert intervals[0][1] > -3
    assert intervals[1][0] < -3


def test_profile_helpers_reject_invalid_samples_and_offsets():
    samples = [Point(10, 0), Point(10, -1)]

    with pytest.raises(ValueError, match="strictly ordered"):
        ReachableProfile(list(reversed(samples)))
    with pytest.raises(ValueError, match="finite and non-negative"):
        ReachableProfile(samples).offset(float("nan"))
    profile = ReachableProfile(samples)
    assert profile.value_at(-0.5) == pytest.approx(10)
    with pytest.raises(ValueError, match="outside"):
        profile.value_at(1)
