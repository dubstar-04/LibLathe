import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import RoutingDirection

TOLERANCE = 1e-5


class PartoffOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate the path for the Part operation"""

        self._begin_generation()
        limits = self.containment
        face = limits.ZMax
        tool_bounds = self.tool.get_segmentgroup().boundbox()

        if self.partSegmentGroup.count() and self.partSegmentGroup.boundbox().ZMin < face - TOLERANCE:
            raise ValueError("Parting face (containment maximum Z) must not be inside the part")
        if limits.ZLength() < tool_bounds.ZLength() - TOLERANCE:
            raise ValueError("Parting containment must be at least as wide as the tool")

        # Place the tool's +Z edge on the face so the whole tool stays on the stock side.
        z = face - tool_bounds.ZMax
        if not limits.ZMin - TOLERANCE <= z <= face + TOLERANCE:
            raise ValueError("Tool reference must lie within the tool's axial extent")

        # TODO: Add a chip break / pecking option

        segmentgroup = SegmentGroup()
        segmentgroup.addSegment(Segment(Point(limits.XMax, z), Point(limits.XMin, z)))
        self.tool_paths.append(segmentgroup)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        return self._route_paths(self.tool_paths, protect_part=False, direction=RoutingDirection.RADIAL)
