import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path


class PartoffOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the Part operation"""

        self.tool_paths = []
        XMin = self.containment.XMin
        XMax = self.containment.XMax
        ZMin = self.containment.ZMin

        # TODO: Add a chip break / pecking option

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

        try:
            for segmentgroup in self.tool_paths:
                path.fromSegmentGroup(self, segmentgroup)
        except (ValueError, RuntimeError):
            self.tool_paths = []
            raise

        return path.commands
