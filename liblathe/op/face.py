import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path


class FaceOP(liblathe.op.base.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""
        part_boundbox = self.part_segment_group.boundbox()

        x_min = self.min_dia * 0.5
        x_max = self.stock.x_max + self.extra_dia * 0.5 + self.clearance
        z_min = part_boundbox.z_max + self.stock_to_leave
        z_max = self.stock.z_max + self.start_offset

        self.clearing_paths = []

        # TODO: Move the final pass to finishing passes for a slower pass
        # work backwards from z_min to z_max adding a segmentgroup for each stepover
        z_pos = z_min
        while z_pos < z_max:
            segmentgroup = SegmentGroup()
            pt1 = Point(x_max, z_pos)
            pt2 = Point(x_min, z_pos)
            seg = Segment(pt1, pt2)
            segmentgroup.add_segment(seg)

            pt3 = pt2.project(self.leadout_angle, self.step_over)
            leadout = Segment(pt2, pt3)
            segmentgroup.add_segment(leadout)
            z_pos += self.step_over
            self.clearing_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in reversed(self.clearing_paths):
            path.from_segment_group(self, segmentgroup)

        return path.commands
