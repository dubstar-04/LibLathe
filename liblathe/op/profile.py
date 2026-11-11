import math

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class ProfileOP(liblathe.op.base.BaseOP):

    def __init__(self):
        super().__init__()
        self.leadin_angle = 0

    def _trim_entry(self, contour, radius):
        """Join an axial entry to the first intersection with the offset polyline."""
        segments = contour.getSegments()
        for index, segment in enumerate(segments):
            low, high = sorted((segment.start.X, segment.end.X))
            if low <= radius <= high:
                dx = segment.end.X - segment.start.X
                fraction = (radius - segment.start.X) / dx if dx else 0
                entry = Point(radius, segment.start.Z + fraction * (segment.end.Z - segment.start.Z))
                result = SegmentGroup()
                if not entry.isSame(segment.end):
                    result.addSegment(Segment(entry, segment.end))
                for remaining in segments[index + 1:]:
                    result.addSegment(remaining)
                return result
        raise ValueError("Profile offset does not intersect its axial lead-in")

    def _profile_offsets(self, base):
        """Generate fixed normal offsets meeting regularly spaced axial entries."""
        step = float(self.pass_offset)
        if not math.isfinite(step) or step <= 0:
            raise ValueError("pass_offset must be finite and positive")
        if isinstance(self.finish_passes, bool) or not isinstance(self.finish_passes, int) or self.finish_passes < 0:
            raise ValueError("finish_passes must be a non-negative integer")
        if not self.finish_passes:
            return
        datum = base.getSegments()[0].start.X
        for index in range(self.finish_passes):
            distance = step * index
            contour = base.offset(distance, extend_start=True)
            yield self._trim_entry(contour, datum + distance)

    def generatePath(self):
        """Replace toolpaths on success; leave no published paths on failure."""
        self.tool_paths = []
        tool_paths = []
        # get the defeature part profile
        profileSegmentGroup = self._defeature_profile(self.allow_grooving)
        # internal segment group to check if intersects the part. use a small offset to reduce false positives
        internalOffset = profileSegmentGroup.offset(-0.1)

        # define the base segment group using the stock to leave as a datum
        base_segmentGroup = profileSegmentGroup.offset(self.stock_to_leave, extend_start=True)
        datum = profileSegmentGroup.getSegments()[0].start.X
        front = base_segmentGroup.getSegments()[0].start
        if front.X > datum:
            extended = SegmentGroup()
            extended.addSegment(Segment(Point(datum, front.Z), front))
            extended.extend(base_segmentGroup)
            base_segmentGroup = extended
        tool = self.tool.get_segmentgroup()
        for offset in self._profile_offsets(base_segmentGroup):
            for stroke in self._clip_path(offset):
                segments = stroke.getSegments()
                segmentgroup = SegmentGroup()
                self._add_lead(segmentgroup, segments[0].start, self.leadin_angle,
                               self.containment, lead_in=True)
                segmentgroup.extend(stroke)
                self._add_lead(segmentgroup, segments[-1].end, self.leadout_angle,
                               self.containment)
                if segmentgroup.intersectsGroup(internalOffset):
                    raise ValueError("Calculated profile path intersects part")
                for segment in segmentgroup.getSegments():
                    self.partSegmentGroup.validateToolSweep(tool, segment.start, segment.end)
                tool_paths.append(segmentgroup)

        self.tool_paths = tool_paths
