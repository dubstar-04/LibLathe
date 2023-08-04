import math
from collections import namedtuple

import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup

# create a namedtuple to hold intersection data
Intersection = namedtuple('Intersection', 'point, seg')


class RoughOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the Rough operation"""
        roughing_segment_group = self.part_segment_group.defeature(self.stock.z_min, self.tool, self.allow_grooving)
        # self.part_segment_group.create_freecad_shape('roughing_segment_group')
        self.clearing_paths = []
        z_max = self.stock.z_max + self.start_offset + self.clearance
        z_min = z_max - self.stock.z_length() - self.start_offset - self.clearance
        # create roughing boundary offset by the stock to leave value
        # include a minimal offset to ensure the roughing passes don't intersect the part
        offset = 0.01 + self.stock_to_leave
        roughing_boundary = roughing_segment_group.offset_path(offset)
        # define the x limit for roughing
        x_min = -abs(math.ceil(self.stock.x_length() + self.extra_dia * 0.5))

        # start from a small offset to ensure the roughing passes intersect with the roughing_boundary
        # TODO: This is a bit hacky, is there a better way?
        x_pos = -1e-6
        # work from 0 to x_min creating roughing passes
        while x_pos > x_min:
            # check if the roughing pass start is outside the stock
            boundary_z = roughing_boundary.z_at_x(x_pos)
            if boundary_z and round(boundary_z, 5) >= round(self.stock.z_max, 5):
                x_pos -= self.step_over
                continue

            pt1 = Point(x_pos, 0, z_max)
            pt2 = Point(x_pos, 0, z_min)
            path_line = Segment(pt1, pt2)
            intersections = []
            for seg in roughing_boundary.get_segments():
                intersect, point = seg.intersect(path_line)
                if intersect:
                    for p in point:
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
                intersections = sorted(intersections, key=lambda p: p.point.Z, reverse=True)

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
            
            x_pos -= self.step_over

            if segmentgroup.count():
                self.tool_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = []

        for segmentgroup in reversed(self.tool_paths):
            rough = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
            path.extend(rough)

        return path
