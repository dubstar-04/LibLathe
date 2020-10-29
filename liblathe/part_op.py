import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup


class PartOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the Part operation"""

        self.clearing_paths = []

        toolWidth = self.tool.get_width()
        xmin = self.stock.XMin - self.extra_dia
        xmax = 0 - self.min_dia
        zmin = self.stock.ZMin - toolWidth

        # build list of segments
        segmentgroup = SegmentGroup()
        startPt = Point(xmin, 0, zmin)
        endPt = Point(xmax, 0, zmin)
        seg = Segment(startPt, endPt)
        segmentgroup.add_segment(seg)

        self.clearing_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []
        for segmentgroup in self.clearing_paths:
            finish = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.hfeed, self.vfeed)
            Path.append(finish)
        return Path
