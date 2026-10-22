"""Interactive offset example; use --headless to skip the viewer."""

import argparse
import os
import sys
import time

thisFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(thisFolder))

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.debug.debug import Debug


def create_profile(scale=1):
    vertices = [
        (0, 10), (2.36, 9.72), (4.58, 8.89), (6.55, 7.56),
        (8.15, 5.80), (9.28, 3.72), (9.9, 1.42), (9.95, -0.95),
        (9.45, -3.27), (8.41, -5.41), (6.90, -7.24), (5, -9),
        (9.5, -15.85), (5.4, -22), (4.03, -22.68), (3.01, -23.81),
        (2.45, -25.23), (2.45, -26.76), (3.00, -28.18), (4.02, -29.31),
        (5.4, -30), (5.4, -40), (13, -45), (13, -48), (0, -48),
    ]
    points = [Point(x * scale, z * scale) for x, z in vertices]
    group = SegmentGroup()
    for start, end in zip(points, points[1:]):
        group.addSegment(Segment(start, end))
    return group


def create_tool(scale=1):
    points = [Point(0, 0), Point(0, 5 * scale),
              Point(5 * scale, 5 * scale), Point(5 * scale, 0), Point(0, 0)]
    group = SegmentGroup()
    for start, end in zip(points, points[1:]):
        group.addSegment(Segment(start, end))
    return group


def create_stock(group, scale=1):
    bounds = group.boundbox()
    return BoundBox(Point(bounds.XMin, bounds.ZMin - 5 * scale),
                    Point(bounds.XMax + 5 * scale, bounds.ZMax + 5 * scale))


def main(headless=False):
    started = time.perf_counter()
    group = create_profile()
    tool = create_tool()
    stock = create_stock(group)
    print('count', group.count())
    bounds = group.boundbox()
    print('bb:', bounds.XMin, bounds.ZMin, bounds.XMax, bounds.ZMax)
    print('Init time:', time.perf_counter() - started)
    started = time.perf_counter()
    defeatured = group.defeature(stock, tool, True)
    print('Defeature time:', time.perf_counter() - started)
    print('defeatured group size', defeatured.count())
    groups = [group, defeatured, tool]
    for distance in range(1, 5):
        started = time.perf_counter()
        groups.append(defeatured.offset(distance))
        print('Offset time:', distance, ':', time.perf_counter() - started)
    if not headless:
        Debug().draw(groups)
    return groups


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    segmentGroups = main(parser.parse_args().headless)
