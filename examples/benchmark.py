"""Repeatable headless geometry benchmark; write JSON results to stdout."""

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.ex4_performance import create_profile, create_stock, create_tool
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.debug.debug import Debug


CASES = ('example', 'segments_16x', 'dimensions_8x', 'arc_heavy')


def subdivide_lines(group, factor):
    result = SegmentGroup()
    for segment in group.getSegments():
        if segment.bulge != 0:
            raise ValueError('Line subdivision requires a line-only profile')
        points = [segment.start.lerp(segment.end, i / factor)
                  for i in range(factor + 1)]
        for start, end in zip(points, points[1:]):
            result.addSegment(Segment(start, end))
    return result


def arc_profile():
    vertices = [(0, 0), (8, -8), (12, -12), (8, -16),
                (12, -20), (8, -24), (8, -32), (0, -32)]
    group = SegmentGroup()
    for i, (start, end) in enumerate(zip(vertices, vertices[1:])):
        group.addSegment(Segment(Point(*start), Point(*end),
                                 math.tan(math.pi / 8) if i < 5 else 0))
    return group


def measure(operation, describe, warmups, repetitions):
    expected = None
    samples = []
    for i in range(warmups + repetitions):
        started = time.perf_counter() if i >= warmups else None
        result = operation()
        if started is not None:
            samples.append(time.perf_counter() - started)
        output = describe(result)
        if expected is not None and output != expected:
            raise RuntimeError(f'Benchmark output changed: {expected!r} -> {output!r}')
        expected = output
    return result, {
        **expected,
        'median_seconds': statistics.median(samples),
        'p95_seconds': sorted(samples)[math.ceil(0.95 * len(samples)) - 1],
        'samples_seconds': samples,
    }


def run_case(name, warmups, repetitions, render=False):
    scale = 8 if name == 'dimensions_8x' else 1
    multiplier = 16 if name == 'segments_16x' else 1
    group = arc_profile() if name == 'arc_heavy' else create_profile(scale)
    if multiplier != 1:
        group = subdivide_lines(group, multiplier)
    tool = create_tool(scale)
    stock = create_stock(group, scale)
    describe = lambda result: {'output_segments': result.count()}
    defeatured, defeature = measure(
        lambda: group.defeature(stock, tool, True), describe, warmups, repetitions)
    defeature['input_segments'] = group.count()
    # Keep arcs in the SDF workload; defeaturing turns them into line segments.
    source = group if name == 'arc_heavy' else defeatured
    if multiplier != 1:
        source = subdivide_lines(source, multiplier)
    offsets = []
    previews = [group, defeatured, tool]
    for distance in range(1, 5):
        result, timing = measure(lambda: source.offset(distance), describe,
                                 warmups, repetitions)
        offsets.append({'distance': distance, 'input_segments': source.count(),
                        **timing})
        previews.append(result)
    report = {
        'name': name,
        'dimension_scale': scale,
        'segment_multiplier': multiplier,
        'offset_source': 'original_arc_profile' if name == 'arc_heavy' else 'defeatured',
        'defeature': defeature,
        'offsets': offsets,
    }
    if render:
        def render_preview():
            image = Debug().render(previews)
            size = image.size
            image.close()
            return size

        _, report['render'] = measure(
            render_preview, lambda size: {'width': size[0], 'height': size[1]},
            warmups, repetitions)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-type', required=True,
                        help='Label of the build used for the imported C++ extensions')
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--repetitions', type=int, default=5)
    parser.add_argument('--cases', nargs='+', choices=CASES, default=list(CASES))
    parser.add_argument('--render', action='store_true',
                        help='Time preview rendering separately; never open a viewer')
    args = parser.parse_args(argv)
    if args.warmups < 1 or args.repetitions < 2:
        parser.error('use at least one warm-up and two measured repetitions')
    report = {
        'schema_version': 1,
        'environment': {
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'platform': platform.platform(),
            'machine': platform.machine(),
            'build_type': args.build_type,
            'build_type_source': 'command_line',
        },
        'settings': {
            'clock': 'perf_counter',
            'warmups': args.warmups,
            'repetitions': args.repetitions,
            'p95_method': 'nearest_rank',
            'rendering': args.render,
        },
        'cases': [run_case(name, args.warmups, args.repetitions, args.render)
                  for name in args.cases],
    }
    json.dump(report, sys.stdout, indent=2, allow_nan=False)
    print()


if __name__ == '__main__':
    main()
