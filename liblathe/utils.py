import math

from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup


class Intersection:
    def __init__(self, point, segment):
        self.point = point
        self.seg = segment


def sort_intersections_z(intersections):
    """ sort the a list of intersections by their z position """

    sortedPoints = sorted(intersections, key=lambda p: p.point.Z, reverse=True)
    return sortedPoints


def remove_the_groove(segmentgroupIn, stock_zmin, tool):
    segments = segmentgroupIn.get_segments()
    segs_out = SegmentGroup()
    index = 0
    while index < len(segments):
        seg = segments[index]

        if seg.bulge != 0:
            if seg.bulge > 0:
                seg = Segment(seg.start, seg.end)

            segs_out.add_segment(seg)

        if seg.bulge == 0:
            pt1 = seg.start
            pt2 = seg.end
            # print('seg angle', segments.index(seg), pt1.angle_to(pt2))
            if pt1.angle_to(pt2) > tool.get_tool_cutting_angle():
                next_index, pt = find_next_good_edge(segments, index, stock_zmin, tool)
                if not next_index:
                    seg = Segment(pt1, pt)
                    segs_out.add_segment(seg)
                    break
                if next_index != index:
                    seg = Segment(pt1, pt)
                    segs_out.add_segment(seg)
                    next_pt1 = pt
                    next_pt2 = segments[next_index].end
                if next_pt1 != pt:
                    seg = Segment(pt1, next_pt2)
                    segs_out.add_segment(seg)
                    next_index += 1

                index = next_index
                continue
            else:
                segs_out.add_segment(seg)

        index += 1
    return segs_out


def find_next_good_edge(segments, current_index, stock_zmin, tool):
    index = current_index
    pt1 = segments[index].start
    index += 1
    while index < len(segments):
        # create a new point at the max angle from pt1
        ang = tool.get_tool_cutting_angle()
        # calculate the length required to project the point to the centreline
        length = abs(pt1.X / math.cos(math.radians(360 - ang)))
        pt2 = pt1.project(ang, length)
        # create a new projected segment
        seg = Segment(pt1, pt2)

        # loop through the remaining segments and see if the projected segments
        idx = index
        while idx < len(segments):
            intersect, pt = seg.intersect(segments[idx])
            if intersect:
                return idx, pt[0]
            idx += 1
        index += 1

    stock_pt = Point(pt1.X, pt1.Y, stock_zmin)
    seg = Segment(pt1, stock_pt)
    index = current_index
    index += 1

    while index < len(segments):
        intersect, point = seg.intersect(segments[index])
        if intersect:
            # print('Utils intersect:', point.X)
            return index, point

        index += 1
    # No solution :(
    # print('find_next_good_edge: FAILED')
    return False, stock_pt
