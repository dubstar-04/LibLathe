import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path


class PartoffOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the Part operation"""

        self.tool_paths = []
        toolShape = self.tool.get_segmentgroup()
        toolBoundbox = toolShape.boundbox()
        toolWidth = toolBoundbox.x_length()

        x_min = self.stock.x_min
        x_max = self.stock.x_max + self.clearance
        z_min = self.stock.z_min - toolWidth

        #TODO: Add a chip break / pecking option

        # build list of segments
        segmentgroup = SegmentGroup()
        startPt = Point(x_max, z_min)
        endPt = Point(x_min, z_min)
        seg = Segment(startPt, endPt)
        segmentgroup.add_segment(seg)

        self.tool_paths.append(segmentgroup)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in self.tool_paths:
            path.from_segment_group(self, segmentgroup)

        return path.commands
