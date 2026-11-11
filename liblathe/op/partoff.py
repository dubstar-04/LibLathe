import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import RoutingDirection


class PartoffOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the Part operation"""

        self._begin_generation()
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

        return self._route_paths(self.tool_paths, protect_part=False, direction=RoutingDirection.RADIAL)
