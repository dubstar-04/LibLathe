import math

import liblathe.op.base
from liblathe.op.base import Direction
from liblathe.base.point import Point
from liblathe.base.boundbox import BoundBox
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import RoutingDirection
from liblathe.op.reachable_profile import ReachableProfile


class RoughOP(liblathe.op.base.BaseOP):

    def __init__(self):
        super().__init__()
        self.direction = Direction.NEGATIVE_Z

    def getParams(self):
        return {**super().getParams(), "direction": self.direction, "mode": self.mode}

    def generatePath(self):
        """Replace toolpaths on success; leave no published paths on failure."""
        self._begin_generation(pass_offset=True, allowance=True)
        if not isinstance(self.direction, Direction):
            raise ValueError("Rough direction must be a Direction enumeration member")
        tool_paths = []
        defeature_result = self._defeature_profile_with_samples(self.allow_grooving)
        roughing_contour = defeature_result.contour

        # internal segment group to check if intersects the part. use a small offset to reduce false positives
        internal_offset = roughing_contour.offset(-0.1)

        # Keep the tool-origin limit reachable from outside the part and leave
        # the requested allowance using the sampled defeature profile.
        profile = ReachableProfile(defeature_result.samples).offset(0.01 + self.stock_to_leave)
        if self.direction == Direction.RADIAL:
            tool_paths = self._generate_radial_paths(profile, internal_offset)
        else:
            tool_paths = self._generate_axial_paths(profile, internal_offset)
        self.tool_paths = tool_paths

    def _generate_axial_paths(self, profile, internal_offset):
        x_min = self.containment.XMin
        x_max = self.containment.XMax
        z_min = self.containment.ZMin
        z_max = self.containment.ZMax
        limits = BoundBox(Point(x_min, z_min), Point(x_max, z_max))
        tool_paths = []

        for x_pos in self._stations(x_min, x_max, self.pass_offset):
            segment_group = SegmentGroup()
            intervals = profile.intervals_below(x_pos)
            first_z = min(profile.samples[0].Z, z_max)
            if intervals and intervals[0][0] <= first_z + 1e-6:
                intervals[0] = (z_max, intervals[0][1])
            elif first_z < z_max - 1e-6:
                intervals.insert(0, (z_max, first_z))

            for high_z, low_z in intervals:
                high_z = min(high_z, z_max)
                low_z = max(low_z, z_min)
                if high_z - low_z < self.pass_offset:
                    continue

                if self.direction == Direction.NEGATIVE_Z:
                    start, end = Point(x_pos, high_z), Point(x_pos, low_z)
                    entry_is_contained = high_z < z_max - 1e-6
                    exit_is_contained = low_z > z_min + 1e-6
                    leadin_angle, leadout_angle = self.leadin_angle, self.leadout_angle
                else:
                    start, end = Point(x_pos, low_z), Point(x_pos, high_z)
                    entry_is_contained = low_z > z_min + 1e-6
                    exit_is_contained = high_z < z_max - 1e-6
                    leadin_angle, leadout_angle = self.leadout_angle, self.leadin_angle

                if entry_is_contained:
                    self._add_lead(segment_group, start, leadin_angle,
                                   limits, lead_in=True)
                segment_group.addSegment(Segment(start, end))
                if exit_is_contained:
                    self._add_lead(segment_group, end, leadout_angle, limits)

            if segment_group.count():
                if segment_group.intersectsGroup(internal_offset):
                    raise ValueError("Calculated roughing path intersects part")

                self.partSegmentGroup.validateToolSweeps(
                    self.tool.get_segmentgroup(),
                    [(segment.start, segment.end) for segment in segment_group.getSegments()])
                tool_paths.append(segment_group)

        return tool_paths

    def _generate_radial_paths(self, profile, internal_offset):
        """Step along -Z, cutting one full radial stroke toward the axis at each station."""
        tool = self.tool.get_segmentgroup()
        tool_bounds = tool.boundbox()
        tool_width = tool_bounds.ZLength()
        if tool_width <= 0:
            raise ValueError("Radial roughing requires a tool with positive axial width")

        # Containment limits the tool reference; the profile keeps the insert clear of the part.
        # Facing leaves room for the pull-off; grooving withdraws along the plunge.
        z_low = max(self.containment.ZMin, profile.samples[-1].Z)
        if self.containment.ZMax < z_low - 1e-6:
            raise ValueError("Radial roughing containment does not reach the reachable profile")
        rise = 0.0 if self.allow_grooving else self._pull_off_rise()
        z_high = max(z_low, self.containment.ZMax - rise)
        z_stations = self._stations_descending(z_high, z_low, min(self.pass_offset, tool_width))
        z_stations = sorted(set(z_stations) | set(self._radial_wall_stations(profile, z_high, z_low)),
                            reverse=True)

        x_min = self.containment.XMin
        x_max = self.containment.XMax
        tool_paths = []
        for z_pos in z_stations:
            if z_pos > profile.samples[0].Z:
                radial_limit = profile.samples[0].X
            else:
                radial_limit = profile.value_at(z_pos)
            end_x = max(x_min, radial_limit)
            if end_x >= x_max - 1e-6:
                continue
            start = Point(x_max, z_pos)
            end = Point(end_x, z_pos)
            stroke = SegmentGroup()
            stroke.addSegment(Segment(start, end))
            self.partSegmentGroup.validateToolSweeps(tool, [(start, end)])
            if not self.allow_grooving:
                stroke.addSegment(Segment(end, self._radial_pull_off(end, tool, internal_offset)))
            if stroke.intersectsGroup(internal_offset):
                raise ValueError("Calculated roughing path intersects part")
            tool_paths.append(stroke)
        return tool_paths

    def _pull_off_rise(self):
        """Return the +Z component of the configured lead-out."""
        return max(0.0, Point(0, 0).project(self.leadout_angle, self.pass_offset).Z)

    def _radial_pull_off(self, end, tool, internal_offset):
        """Return a contained, collision-free facing pull-off point.

        Stations advance along -Z, so material on the +Z side is already cleared.
        Try the configured lead-out, then a pure +Z lift, shortening each until it fits.
        """
        limits = self.containment
        minimum = SegmentGroup.defeatureResolution
        for angle in (self.leadout_angle, math.pi / 2):
            target = end.project(angle, self.pass_offset)
            if target.Z - end.Z <= 1e-9:
                continue
            fraction = min(1.0, (limits.ZMax - end.Z) / (target.Z - end.Z))
            if target.X > end.X:
                fraction = min(fraction, (limits.XMax - end.X) / (target.X - end.X))
            length = fraction * self.pass_offset
            while length >= minimum:
                candidate = end.project(angle, length)
                move = SegmentGroup()
                move.addSegment(Segment(end, candidate))
                if not move.intersectsGroup(internal_offset):
                    try:
                        self.partSegmentGroup.validateToolSweeps(tool, [(end, candidate)])
                    except RuntimeError:
                        pass
                    else:
                        return candidate
                length /= 2
        raise ValueError(
            "Cannot pull the tool off the radial roughing face at Z %.4f without "
            "leaving containment or colliding with the part" % end.Z)

    @staticmethod
    def _radial_wall_stations(profile, z_high, z_low):
        """Return the low-radius stations beside each abrupt wall in the reachable radius.

        Samples run along -Z, so a rise is a wall on the -Z side and a fall is a wall
        on the +Z side. Evenly spaced stations would otherwise stop short of either wall.
        """
        samples = profile.samples
        threshold = SegmentGroup.offsetTolerance
        stations = []
        for index, (current, following) in enumerate(zip(samples, samples[1:])):
            rising = following.X - current.X > threshold
            continued_rise = index > 0 and current.X - samples[index - 1].X > threshold
            if rising and not continued_rise and z_low <= current.Z <= z_high:
                stations.append(current.Z)

            falling = current.X - following.X > threshold
            continued_fall = (index + 2 < len(samples)
                              and following.X - samples[index + 2].X > threshold)
            if falling and not continued_fall and z_low <= following.Z <= z_high:
                stations.append(following.Z)
        return stations

    def generateGCode(self):
        if self.direction == Direction.RADIAL:
            return self._route_paths(self.tool_paths, direction=RoutingDirection.RADIAL,
                                     radial_clearance=self._grooving_clearance())
        return self._route_paths(reversed(self.tool_paths))
