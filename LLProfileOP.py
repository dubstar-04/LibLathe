import math

import LibLathe.LLBaseOP
import LibLathe.LLUtils as utils
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment
from LibLathe.LLSegmentGroup import SegmentGroup


class ProfileOP(LibLathe.LLBaseOP.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""

        if not self.allow_roughing:
            return

        self.clearing_paths = []
        zmax = self.stock.ZMax + self.start_offset
        line_count = int(math.ceil(self.stock.XLength() / self.step_over))
        xstart = 0 - (self.step_over * line_count + self.min_dia)

        roughing_boundary = utils.offsetPath(self.part_segment_group, self.step_over * self.finish_passes)
        self.finishing_paths.append(roughing_boundary)

        for roughing_pass in range(line_count):
            xpt = xstart + roughing_pass * self.step_over
            pt1 = Point(xpt, 0, zmax)
            pt2 = Point(xpt, 0, zmax - self.stock.ZLength() - self.start_offset)
            path_line = Segment(pt1, pt2)
            intersections = []
            for seg in roughing_boundary.get_segments():
                intersect, point = seg.intersect(path_line)
                if intersect:
                    if type(point) is list:
                        for p in point:
                            intersection = utils.Intersection(p, seg)
                            intersections.append(intersection)
                    else:
                        intersection = utils.Intersection(point, seg)
                        intersections.append(intersection)

            # build list of segments
            segmentGroup = SegmentGroup()

            if not intersections:
                seg = path_line
                segmentGroup.add_segment(seg)

            if len(intersections) == 1:
                # Only one intersection, trim line to intersection.
                seg = Segment(pt1, intersections[0].point)
                segmentGroup.add_segment(seg)

            if len(intersections) > 1:
                # more than one intersection
                intersection = utils.Intersection(pt1, None)
                intersections.insert(0, intersection)

                intersection2 = utils.Intersection(pt2, None)
                intersections.append(intersection2)

                intersections = utils.sort_intersections_z(intersections)

                for i in range(len(intersections)):
                    if i + 1 < len(intersections):
                        if intersections[i].seg:
                            if intersections[i].seg.is_same(intersections[i + 1].seg):
                                seg = intersections[i].seg
                                rad = seg.get_radius()

                                if seg.bulge < 0:
                                    rad = 0 - rad

                                path_line = Segment(intersections[i].point, intersections[i + 1].point)
                                path_line.set_bulge_from_radius(rad)

                                segmentGroup.add_segment(path_line)

                        if i % 2 == 0:
                            path_line = Segment(intersections[i].point, intersections[i + 1].point)
                            segmentGroup.add_segment(path_line)

            if segmentGroup.count():
                self.clearing_paths.append(segmentGroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []

        for segmentGroup in self.clearing_paths:
            rough = segmentGroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(rough)
        for segmentGroup in self.finishing_paths:
            finish = segmentGroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(finish)

        return Path
