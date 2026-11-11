import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

class FaceOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Generate inward facing passes, publishing only a complete result."""
        self._begin_generation(pass_offset=True, allowance=True)
        part_boundbox = self.partSegmentGroup.boundbox()

        XMin = self.containment.XMin
        XMax = self.containment.XMax
        ZMin = max(self.containment.ZMin, part_boundbox.ZMax + self.stock_to_leave)
        ZMax = self.containment.ZMax
        clearing_paths = []

        # TODO: Move the final pass to finishing passes for a slower pass
        # work backwards from ZMin to ZMax at the requested axial depth
        for z_pos in self._stations(ZMin, ZMax, self.pass_offset, include_end=True):
            segmentgroup = SegmentGroup()
            pt1 = Point(XMax, z_pos)
            pt2 = Point(XMin, z_pos)
            seg = Segment(pt1, pt2)
            segmentgroup.addSegment(seg)

            pt3 = pt2.project(self.leadout_angle, self.pass_offset)
            leadout = Segment(pt2, pt3)
            segmentgroup.addSegment(leadout)
            clearing_paths.extend(self._clip_path(segmentgroup))
        self.clearing_paths = clearing_paths

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        return self._route_paths(reversed(self.clearing_paths), protect_part=False)
