import math

import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup


class FaceOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""

        partBoundBox = self.part_segment_group.boundbox()
        xmin = self.stock.XMin - self.extra_dia * 0.5
        xmax = 0 - self.min_dia * 0.5
        zmax = self.stock.ZMax + self.start_offset

        self.clearing_paths = []
        length = zmax - partBoundBox.ZMax
        step_over = self.step_over
        line_count = math.ceil(length / step_over)
        zstart = partBoundBox.ZMax + step_over * line_count

        # build list of segments
        segmentgroup = SegmentGroup()

        counter = 0
        while counter < line_count + 1:
            zpt = zstart - counter * self.step_over
            pt1 = Point(xmin, 0, zpt)
            pt2 = Point(xmax, 0, zpt)
            path_line = Segment(pt1, pt2)
            seg = path_line
            segmentgroup.add_segment(seg)
            counter += 1

        self.clearing_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []
        for segmentgroup in self.clearing_paths:
            rough = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(rough)

        return Path
