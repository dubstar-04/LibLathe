import math

import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup


class FaceOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""

        partBoundBox = self.part_segment_group.boundbox()
        x_min = self.stock.x_min - self.extra_dia * 0.5
        x_max = 0 - self.min_dia * 0.5
        z_max = self.stock.z_max + self.start_offset

        self.clearing_paths = []
        length = z_max - partBoundBox.z_max + self.stock_to_leave
        step_over = self.step_over
        line_count = math.ceil(length / step_over)
        zstart = partBoundBox.z_max + step_over * line_count + self.stock_to_leave

        # build list of segments
        segmentgroup = SegmentGroup()
        # TODO: Move the final pass to finishing passes for a slower pass
        counter = 0
        while counter < line_count + 1:
            zpt = zstart - counter * self.step_over
            pt1 = Point(x_min, 0, zpt)
            pt2 = Point(x_max, 0, zpt)
            path_line = Segment(pt1, pt2)
            seg = path_line
            segmentgroup.add_segment(seg)

            pt3 = pt2.project(135, self.step_over)
            leadout = Segment(pt2, pt3)
            segmentgroup.add_segment(leadout)

            counter += 1

        self.clearing_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []
        for segmentgroup in self.clearing_paths:
            rough = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
            Path.append(rough)

        return Path
