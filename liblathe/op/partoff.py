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
        toolWidth = toolBoundbox.XLength()

        XMin = self.stock.XMin
        XMax = self.stock.XMax + self.clearance
        ZMin = self.stock.ZMin - toolWidth

        #TODO: Add a chip break / pecking option

        # build list of segments
        segmentgroup = SegmentGroup()
        startPt = Point(XMax, ZMin)
        endPt = Point(XMin, ZMin)
        seg = Segment(startPt, endPt)
        segmentgroup.addSegment(seg)

        self.tool_paths.append(segmentgroup)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in self.tool_paths:
            path.from_segment_group(self, segmentgroup)

        return path.commands
