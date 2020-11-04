import math
from collections import namedtuple

import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup

# create a namedtuple to hold intersection data
Intersection = namedtuple('Intersection', 'point, seg')


class ProfileOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""

        self.part_segment_group = self.part_segment_group.remove_the_groove(self.stock.ZMin, self.tool, self.allow_grooving)

        if self.allow_finishing and self.finish_passes:
            # If we are allowed finishing passes, add the part segment group to the finishing paths.
            self.finishing_paths.append(self.part_segment_group)
            f_pass = 1
            while f_pass < self.finish_passes:
                segmentgroup = self.part_segment_group.offsetPath(self.step_over * f_pass)
                self.finishing_paths.append(segmentgroup)
                f_pass += 1

        if not self.allow_roughing:
            return

        self.clearing_paths = []
        zmax = self.stock.ZMax + self.start_offset
        line_count = int(math.ceil((self.stock.XLength() + self.extra_dia * 0.5) / self.step_over))
        xstart = 0 - (self.step_over * line_count + self.min_dia * 0.5)

        # create roughing boundary at the last finish pass
        offset = self.finish_passes - 1 if self.finish_passes else 0
        roughing_boundary = self.part_segment_group.offsetPath(self.step_over * offset)
        # self.finishing_paths.append(roughing_boundary)

        for roughing_pass in range(line_count):
            xpt = xstart + roughing_pass * self.step_over
            pt1 = Point(xpt, 0, zmax)
            pt2 = Point(xpt, 0, zmax - self.stock.ZLength() - self.start_offset)
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
                    endPt = startPt.project(135, self.step_over)
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
                            if intersections[i].seg:
                                endPt = intersections[i].point
                                startPt = endPt.project(180, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.add_segment(path_line)

                            # primary intersect - intersection[i].point == startpoint
                            path_line = Segment(intersections[i].point, intersections[i + 1].point)
                            segmentgroup.add_segment(path_line)

                            if intersections[i + 1].seg:
                                startPt = intersections[i + 1].point
                                endPt = startPt.project(135, self.step_over)
                                path_line = Segment(startPt, endPt)
                                segmentgroup.add_segment(path_line)

            if segmentgroup.count():
                self.clearing_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []

        for segmentgroup in self.clearing_paths:
            rough = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(rough)
        for segmentgroup in self.finishing_paths:
            finish = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(finish)

        return Path
