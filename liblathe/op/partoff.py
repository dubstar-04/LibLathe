import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path


class PartoffOP(liblathe.op.base.BaseOP):

    def generate_path(self):
        """Generate the path for the Part operation"""

        self.tool_paths = []

        toolWidth = self.tool.get_width()
        
        x_min = self.min_dia * 0.5
        x_max = self.stock.x_max + self.extra_dia * 0.5 + self.clearance
        z_min = self.stock.z_min - toolWidth

        # build list of segments
        segmentgroup = SegmentGroup()
        startPt = Point(x_max, z_min)
        endPt = Point(x_min, z_min)
        seg = Segment(startPt, endPt)
        segmentgroup.add_segment(seg)

        self.tool_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in self.tool_paths:
            path.from_segment_group(self, segmentgroup)

        return path.commands
