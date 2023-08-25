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

    def generate_path(self):
        """Generate the path for the Rough operation"""
        roughing_segment_group = self.part_segment_group.defeature(self.stock, self.tool.get_shape_group(), self.allow_grooving)

        self.clearing_paths = []
        z_max = self.stock.z_max + self.start_offset + self.clearance
        z_min = z_max - self.stock.z_length() - self.start_offset - self.clearance

        # create roughing boundary offset by the stock to leave value
        # include a minimal offset to ensure the roughing passes don't intersect the part
        offset = 0.01 + self.stock_to_leave
        roughing_boundary = roughing_segment_group.offset(offset)

        # define the x limits for roughing
        x_min = self.min_dia * 0.5
        x_max = math.ceil(self.stock.x_length() + self.extra_dia * 0.5)

        # The roughing boundary may have a small x delta from 0 due to being offset. consider it when calculating the x_min pos.
        roughing_boundary_x = roughing_boundary.get_segments()[0].start.x
        # start from a small offset to ensure the roughing passes intersect with the roughing_boundary
        # TODO: This is a bit hacky, is there a better way?
        x_pos = max(1e-6, x_min, roughing_boundary_x)
        # work from 0 to x_min creating roughing passes
        while x_pos < x_max:
            # check if the roughing pass start is outside the stock
            # boundary_z = self.stock.z_max + 5  #roughing_boundary.z_at_x(x_pos)
            # if boundary_z and round(boundary_z, 5) >= round(self.stock.z_max, 5):
            #    x_pos += self.step_over
            #    continue

            pt1 = Point(x_pos, z_max)
            pt2 = Point(x_pos, z_min)
            path_line = Segment(pt1, pt2)
            intersections = []
            for seg in roughing_boundary.get_segments():
                points = seg.intersect(path_line)
                if len(points):
                    for p in points:
                        intersection = Intersection(p, seg)
                        intersections.append(intersection)

            # build list of segments
            segmentgroup = SegmentGroup()

            if not intersections:
                seg = path_line
                segmentgroup.add_segment(seg)

            if len(intersections) == 1:
                # Only one intersection, trim line to intersection.
                seg = Segment(pt1, intersections[0].point)
                segmentgroup.add_segment(seg)
                if intersections[0].seg:
                    # add lead out
                    startPt = intersections[0].point
                    endPt = startPt.project(self.leadout_angle, self.step_over)
                    path_line = Segment(startPt, endPt)
                    segmentgroup.add_segment(path_line)

            if len(intersections) > 1:
                # more than one intersection
                # add the end points of the pass to generate new segments
                intersection = Intersection(pt1, None)
                intersections.insert(0, intersection)

                intersection2 = Intersection(pt2, None)
                intersections.append(intersection2)

                #  sort the a list of intersections by their z position
                intersections = sorted(intersections, key=lambda p: p.point.z, reverse=True)

                for i in range(len(intersections)):
                    if i + 1 < len(intersections):
                        if i % 2 == 0:
                            # primary segment
                            primary_segment = Segment(intersections[i].point, intersections[i + 1].point)

                            # check the length of the pass before adding to the segmentgroup
                            if primary_segment.get_length() < self.step_over:
                                continue

                            # if the intersection is connected to another segment
                            if intersections[i].seg:
                                # add a lead in
                                # TODO: optimise this to match the max tool angle
                                endPt = intersections[i].point
                                startPt = endPt.project(self.leadin_angle, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.add_segment(path_line)

                            # add the primary segment to the segment group
                            segmentgroup.add_segment(primary_segment)

                            # if the intersection is connected to another segment
                            if intersections[i + 1].seg:
                                # add a lead out
                                startPt = intersections[i + 1].point
                                endPt = startPt.project(self.leadout_angle, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.add_segment(path_line)

            x_pos += self.step_over

            if segmentgroup.count():
                if segmentgroup.intersects_group(self.part_segment_group):
                    # Debug().draw([segmentgroup, self.part_segment_group, roughing_boundary])
                    raise ValueError("Calculated roughing path intersects part")

                self.tool_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in reversed(self.tool_paths):
            path.from_segment_group(self, segmentgroup)

        return path.commands
