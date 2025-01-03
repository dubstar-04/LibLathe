import math

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path


class FaceOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the profile operation"""
        part_boundbox = self.partSegmentGroup.boundbox()

        XMin = self.stock.XMin
        XMax = self.stock.XMax + self.clearance
        ZMin = part_boundbox.ZMax + self.stock_to_leave
        ZMax = math.ceil(self.stock.ZMax) + self.step_over
        self.clearing_paths = []

        # TODO: Move the final pass to finishing passes for a slower pass
        # work backwards from ZMin to ZMax adding a segmentgroup for each stepover
        z_pos = ZMin
        while z_pos < ZMax:
            segmentgroup = SegmentGroup()
            pt1 = Point(XMax, z_pos)
            pt2 = Point(XMin, z_pos)
            seg = Segment(pt1, pt2)
            segmentgroup.addSegment(seg)

            pt3 = pt2.project(self.leadout_angle, self.step_over)
            leadout = Segment(pt2, pt3)
            segmentgroup.addSegment(leadout)
            z_pos += self.step_over
            self.clearing_paths.append(segmentgroup)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in reversed(self.clearing_paths):
            path.from_segment_group(self, segmentgroup)

        return path.commands
