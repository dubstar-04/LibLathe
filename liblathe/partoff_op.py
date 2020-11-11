import liblathe.base_op
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup


class PartoffOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the Part operation"""

        self.tool_paths = []

        toolWidth = self.tool.get_width()
        xmin = self.stock.XMin - self.extra_dia * 0.5
        xmax = 0 - self.min_dia * 0.5
        zmin = self.stock.ZMin - toolWidth

        # build list of segments
        segmentgroup = SegmentGroup()
        startPt = Point(xmin, 0, zmin)
        endPt = Point(xmax, 0, zmin)
        seg = Segment(startPt, endPt)
        segmentgroup.add_segment(seg)

        self.tool_paths.append(segmentgroup)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        Path = []
        for segmentgroup in self.tool_paths:
            finish = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
            Path.append(finish)
        return Path
