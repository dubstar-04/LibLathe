from enum import Enum

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import RoutingDirection

# Offset contours are simplified at this resolution, so an offset running along an
# axial entry line may wander from it by up to this distance.
_OFFSET_RESOLUTION = 0.01


class ProfileDirection(Enum):
    NEGATIVE_Z = "-Z"
    POSITIVE_Z = "+Z"
    RADIAL = "Radial"


class ProfileOP(liblathe.op.base.BaseOP):

    def __init__(self):
        super().__init__()
        self.leadin_angle = 0
        self.direction = ProfileDirection.NEGATIVE_Z

    def getParams(self):
        return {**super().getParams(), "direction": self.direction, "mode": self.mode}

    def _trim_entry(self, contour, radius):
        """Join an axial entry to the first point where the offset polyline meets it."""
        segments = contour.getSegments()
        for index, segment in enumerate(segments):
            start_gap = segment.start.X - radius
            end_gap = segment.end.X - radius
            if abs(start_gap) <= _OFFSET_RESOLUTION:
                fraction = 0
            elif start_gap * end_gap <= 0:
                fraction = start_gap / (start_gap - end_gap)
            else:
                continue
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
        self._validate_parameters(pass_offset=True, finish_passes=True)
        step = self.pass_offset
        if not self.finish_passes:
            return
        datum = base.getSegments()[0].start.X
        for index in range(self.finish_passes):
            distance = step * index
            contour = base.offset(distance, extend_start=True)
            yield self._trim_entry(contour, datum + distance)

    def generatePath(self):
        """Replace toolpaths on success; leave no published paths on failure."""
        self._begin_generation(pass_offset=True, finish_passes=True, allowance=True)
        if not isinstance(self.direction, ProfileDirection):
            raise ValueError("Profile direction must be a ProfileDirection enumeration member")
        tool_paths = []
        profile_contour = self._defeature_profile(self.allow_grooving)
        if self.mode == liblathe.op.base.MachiningMode.INTERNAL:
            profile_contour = self._trim_internal_contour(profile_contour)
        internal_offset = profile_contour.offset(-0.1)

        base_contour = profile_contour.offset(self.stock_to_leave, extend_start=True)
        datum = profile_contour.getSegments()[0].start.X
        front = base_contour.getSegments()[0].start
        if front.X > datum:
            extended = SegmentGroup()
            extended.addSegment(Segment(Point(datum, front.Z), front))
            extended.extend(base_contour)
            base_contour = extended
        tool = self.tool.get_segmentgroup()
        internal = self.mode == liblathe.op.base.MachiningMode.INTERNAL
        # Internal radial passes retrace the -Z pass from the bore floor out through the mouth.
        reverse_pass = self.direction == ProfileDirection.RADIAL and internal
        add_leads = self.direction != ProfileDirection.RADIAL or internal
        for offset in self._profile_offsets(base_contour):
            for clipped_stroke in self._clip_path(offset):
                if self.direction == ProfileDirection.RADIAL and not internal:
                    strokes = self._inward_strokes(clipped_stroke)
                elif self.direction == ProfileDirection.POSITIVE_Z:
                    strokes = [clipped_stroke.reversed()]
                else:
                    strokes = [clipped_stroke]

                for stroke in strokes:
                    segment_group = SegmentGroup()
                    segments = stroke.getSegments()
                    if add_leads:
                        if self.direction == ProfileDirection.POSITIVE_Z:
                            leadin_angle, leadout_angle = self.leadout_angle, self.leadin_angle
                        else:
                            leadin_angle, leadout_angle = self.leadin_angle, self.leadout_angle
                        self._add_lead(segment_group, segments[0].start, leadin_angle,
                                       self.containment, lead_in=True)
                    segment_group.extend(stroke)
                    if add_leads:
                        self._add_lead(segment_group, segments[-1].end, leadout_angle,
                                       self.containment)
                    if reverse_pass:
                        segment_group = segment_group.reversed()
                    if segment_group.intersectsGroup(internal_offset):
                        raise ValueError("Calculated profile path intersects part")
                    self.partSegmentGroup.validateToolSweeps(
                        tool, [(segment.start, segment.end)
                               for segment in segment_group.getSegments()])
                    tool_paths.append(segment_group)

        self.tool_paths = tool_paths

    def _trim_internal_contour(self, contour):
        """Discard the scan closure across the open mouth of an internal profile."""
        part_min = self.partSegmentGroup.boundbox().XMin
        contour_bounds = contour.boundbox()
        result = SegmentGroup()
        for segment in contour.getSegments():
            clipped = self._clip(
                segment, part_min, contour_bounds.XMax,
                contour_bounds.ZMin - 1, contour_bounds.ZMax + 1)
            if clipped is not None:
                result.addSegment(clipped)
        if not result.count():
            raise ValueError("Internal profile has no compensated contour at the selected bore")
        return result

    def generateGCode(self):
        if self.direction == ProfileDirection.RADIAL:
            return self._route_paths(reversed(self.tool_paths), direction=RoutingDirection.RADIAL,
                                     radial_clearance=self._grooving_clearance())
        return self._route_paths(reversed(self.tool_paths))
