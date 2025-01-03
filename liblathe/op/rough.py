import math
from collections import namedtuple

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path

# create a namedtuple to hold intersection data
Intersection = namedtuple('Intersection', 'point, seg')


class RoughOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the Rough operation"""
        roughing_segment_group = self.partSegmentGroup.defeature(self.stock, self.tool.get_segmentgroup(), self.allow_grooving)

        # internal segment group to check if intersects the part. use a small offset to reduce false positives
        internal_offset = roughing_segment_group.offset(-0.1)

        self.clearing_paths = []
        ZMax = self.stock.ZMax
        ZMin = self.stock.ZMin

        # create roughing boundary offset by the stock to leave value
        # include a minimal offset to ensure the roughing passes don't intersect the part
        offset = 0.01 + self.stock_to_leave
        roughing_boundary = roughing_segment_group.offset(offset)

        # define the x limits for roughing
        XMin = self.stock.XMin
        XMax = math.ceil(self.stock.XMax)

        # The roughing boundary may have a small x delta from 0 due to being offset. consider it when calculating the XMin pos.
        roughing_boundary_x = roughing_boundary.getSegments()[0].start.X
        # start from a small offset to ensure the roughing passes intersect with the roughing_boundary
        # TODO: This is a bit hacky, is there a better way?
        x_pos = max(1e-6, XMin, roughing_boundary_x)
        # work from 0 to XMin creating roughing passes
        print('XMin:', XMin, 'XMax:', XMax, 'x_pos:', x_pos)
        while x_pos < XMax:
            # check if the roughing pass start is outside the stock
            # boundary_z = self.stock.ZMax + 5  #roughing_boundary.Z_at_x(x_pos)
            # if boundary_z and round(boundary_z, 5) >= round(self.stock.ZMax, 5):
            #    x_pos += self.step_over
            #    continue

            pt1 = Point(x_pos, ZMax)
            pt2 = Point(x_pos, ZMin)
            path_line = Segment(pt1, pt2)
            intersections = []
            for seg in roughing_boundary.getSegments():
                points = seg.intersect(path_line)
                if len(points):
                    for p in points:
                        intersection = Intersection(p, seg)
                        intersections.append(intersection)

            # build list of segments
            segmentgroup = SegmentGroup()

            if not intersections:
                seg = path_line
                # add passes with no intersections only if they're outside the part radius
                if x_pos >= roughing_boundary.boundbox().XMax:
                    segmentgroup.addSegment(seg)

            if len(intersections) == 1:
                # Only one intersection, trim line to intersection.
                seg = Segment(pt1, intersections[0].point)
                segmentgroup.addSegment(seg)
                if intersections[0].seg:
                    # add lead out
                    startPt = intersections[0].point
                    endPt = startPt.project(self.leadout_angle, self.step_over)
                    path_line = Segment(startPt, endPt)
                    segmentgroup.addSegment(path_line)

            if len(intersections) > 1:
                # more than one intersection
                # add the end points of the pass to generate new segments
                if not roughing_boundary.isInside(pt1):
                    intersection = Intersection(pt1, None)
                    intersections.insert(0, intersection)

                if not roughing_boundary.isInside(pt2):
                    intersection2 = Intersection(pt2, None)
                    intersections.append(intersection2)

                #  sort the a list of intersections by their z position
                intersections = sorted(intersections, key=lambda p: p.point.Z, reverse=True)

                for i in range(len(intersections)):
                    if i + 1 < len(intersections):
                        if i % 2 == 0:
                            # primary segment
                            primary_segment = Segment(intersections[i].point, intersections[i + 1].point)

                            # check the length of the pass before adding to the segmentgroup
                            if primary_segment.getLength() < self.step_over:
                                continue

                            # if the intersection is connected to another segment
                            if intersections[i].seg:
                                # add a lead in
                                # TODO: optimise this to match the max tool angle
                                endPt = intersections[i].point
                                startPt = endPt.project(self.leadin_angle, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.addSegment(path_line)

                            # add the primary segment to the segment group
                            segmentgroup.addSegment(primary_segment)

                            # if the intersection is connected to another segment
                            if intersections[i + 1].seg:
                                # add a lead out
                                startPt = intersections[i + 1].point
                                endPt = startPt.project(self.leadout_angle, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.addSegment(path_line)

            x_pos += self.step_over

            if segmentgroup.count():
                if segmentgroup.intersectsGroup(internal_offset):
                    # Debug().draw([segmentgroup, self.partSegmentGroup, roughing_boundary])
                    raise ValueError("Calculated roughing path intersects part")

                self.tool_paths.append(segmentgroup)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in reversed(self.tool_paths):
            path.from_segment_group(self, segmentgroup)

        return path.commands
