import math

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import Path, RoutingDirection


class GrooveOP(liblathe.op.base.BaseOP):
    """Radial grooving: X-only plunges at evenly spaced Z stations, one depth layer at a time,
    followed by finish_passes spring passes along the final contour."""

    # matches the defeature scan resolution
    sample_resolution = 0.01
    # matches the native SegmentGroup::offsetTolerance contour accuracy limit
    offset_tolerance = 0.05
    # overlap between adjacent plunges as a percentage of the tool's axial width
    overlap_percent = 10.0

    def get_max_increment(self, tool_bounds):
        """Return the axial station spacing allowed by tool width and overlap."""
        tool_width = tool_bounds.ZLength()
        if tool_width <= 0:
            raise ValueError("Grooving tool must have a positive axial width")
        return tool_width * (1 - self.overlap_percent / 100)

    def get_z_range(self, tool_bounds):
        """Return the tool-origin Z range that keeps the tool footprint inside the stock Z limits."""
        z_high = self.stock.ZMax - tool_bounds.ZMax
        z_low = self.stock.ZMin - tool_bounds.ZMin
        if z_high - z_low < -1e-6:
            raise ValueError("Grooving range is narrower than the tool width")
        return z_high, min(z_low, z_high)

    @staticmethod
    def get_z_stations(z_high, z_low, max_increment):
        """Return evenly spaced Z stations from z_high to z_low, both ends included.

        Equal increments no larger than max_increment avoid a thin final pass.
        """
        z_range = z_high - z_low
        if z_range <= 1e-6:
            return [z_high]
        count = max(1, math.ceil(z_range / max_increment - 1e-9))
        increment = z_range / count
        return [z_high - i * increment for i in range(count)] + [z_low]

    def _radial_limit(self, boundary, z, x_top, x_min):
        """Return the first accessible tool-origin X travelling inward from x_top at z."""
        path_line = Segment(Point(x_top, z), Point(x_min, z))
        hits = [point.X for seg in boundary.getSegments() for point in seg.intersect(path_line)]
        if hits:
            return max(max(hits), x_min)
        if boundary.isInside(Point(x_min, z)):
            # the whole radial line lies inside the part: nothing to cut
            return x_top
        return x_min

    @staticmethod
    def _clip(segment, x_min, x_max, z_low, z_high):
        """Return the part of a line segment inside the X and Z limits, or None."""
        start, end = segment.start, segment.end
        t_start, t_end = 0.0, 1.0
        for delta, room in ((end.X - start.X, x_max - start.X), (start.X - end.X, start.X - x_min),
                            (end.Z - start.Z, z_high - start.Z), (start.Z - end.Z, start.Z - z_low)):
            if abs(delta) < 1e-12:
                if room < 0:
                    return None
            elif delta > 0:
                t_end = min(t_end, room / delta)
            else:
                t_start = max(t_start, room / delta)
        if t_end - t_start <= 1e-9:
            return None
        return Segment(start.lerp(end, t_start), start.lerp(end, t_end))

    @staticmethod
    def _get_finish_strokes(finish):
        """Split the contour at gaps and X reversals, orienting every stroke inward."""
        strokes = []
        run = SegmentGroup()
        direction = 0
        previous = None
        for segment in finish.getSegments():
            dx = segment.end.X - segment.start.X
            sign = (dx > 0) - (dx < 0)
            if previous is not None and (
                    not previous.end.isSame(segment.start)
                    or (sign and direction and sign != direction)):
                strokes.append(run.reversed() if direction > 0 else run)
                run = SegmentGroup()
                direction = 0
            run.addSegment(segment)
            if sign:
                direction = sign
            previous = segment
        if run.count():
            strokes.append(run.reversed() if direction > 0 else run)
        return strokes

    def generatePath(self):
        """Replace toolpaths on success; leave no published paths on failure."""
        self.tool_paths = []
        radial_step = float(self.pass_offset)
        if not math.isfinite(radial_step) or radial_step <= 0:
            raise ValueError("pass_offset must be finite and positive")
        if isinstance(self.finish_passes, bool) or not isinstance(self.finish_passes, int) or self.finish_passes < 0:
            raise ValueError("finish_passes must be a non-negative integer")

        tool = self.tool.get_segmentgroup()
        tool_bounds = tool.boundbox()
        contact = tool.getRadialContactPoint()

        groove_profile = self.partSegmentGroup.defeature(self.stock, tool, True)
        internal_offset = groove_profile.offset(-0.1)
        boundary = groove_profile.offset(0.01 + self.stock_to_leave)

        x_top = self.stock.XMax - contact.X
        x_min = self.stock.XMin - contact.X
        x_clear = self._x_clear(tool_bounds)
        max_increment = self.get_max_increment(tool_bounds)
        z_high, z_low = self.get_z_range(tool_bounds)

        limits = {}

        def limit_at(z):
            if z not in limits:
                limits[z] = self._radial_limit(boundary, z, x_top, x_min)
            return limits[z]

        # sample the accessible depth at the defeature resolution to find groove walls
        samples = self.get_z_stations(z_high, z_low, self.sample_resolution)
        sample_limits = [limit_at(z) for z in samples]

        # region ends may move inward this far to avoid ill-conditioned wall hits
        wall_window = max(1, int(round(self.offset_tolerance / self.sample_resolution)))
        # classify runs by the deepest nearby limit so a single wall sample cannot form its own run;
        # plunge ends still use the exact limit at each station
        class_limits = [min(sample_limits[max(0, index - wall_window):index + wall_window + 1])
                        for index in range(len(sample_limits))]

        tool_paths = []
        layer_top = x_top
        while True:
            target = layer_top - radial_step
            runs = self._get_runs(class_limits, layer_top, target)
            if not runs:
                break

            layer = SegmentGroup()
            for first, last in runs:
                # runs are classified with a window either side, so search up to two windows inward
                high = self._region_end(sample_limits, first, last, 1, 2 * wall_window)
                low = self._region_end(sample_limits, last, high, -1, 2 * wall_window)
                for z in self.get_z_stations(samples[high], samples[low], max_increment):
                    limit = limit_at(z)
                    if limit >= layer_top - 1e-6:
                        continue
                    end = max(target, limit)
                    # certify the plunge and withdrawal against the full part
                    self.partSegmentGroup.validateToolSweep(tool, Point(x_clear, z), Point(end, z))
                    layer.addSegment(Segment(Point(layer_top, z), Point(end, z)))

            if layer.count():
                if layer.intersectsGroup(internal_offset):
                    raise ValueError("Calculated grooving path intersects part")
                tool_paths.append(layer)
            layer_top = target

        # spring passes follow the final contour to remove plunge scallops on sloped or curved walls
        finish = SegmentGroup()
        for segment in boundary.getSegments():
            clipped = self._clip(segment, x_min, x_top, z_low, z_high)
            if clipped is not None:
                finish.addSegment(clipped)
        if finish.count() and self.finish_passes:
            if finish.intersectsGroup(internal_offset):
                raise ValueError("Calculated grooving finish path intersects part")
            strokes = self._get_finish_strokes(finish)
            for stroke in strokes:
                for segment in stroke.getSegments():
                    self.partSegmentGroup.validateToolSweep(tool, segment.start, segment.end)
            for _ in range(self.finish_passes):
                tool_paths.extend(strokes)

        self.tool_paths = tool_paths

    @staticmethod
    def _get_runs(limits, layer_top, target):
        """Return (first, last) sample index runs that this layer cuts.

        Runs are split where the limit changes between clear, partly cut (above the
        layer target) and fully cut, so stations hug each feature wall.
        """
        def depth_class(limit):
            if limit >= layer_top - 1e-6:
                return 0
            return 1 if limit >= target - 1e-6 else 2

        runs = []
        first = 0
        for index in range(1, len(limits) + 1):
            if index == len(limits) or depth_class(limits[index]) != depth_class(limits[first]):
                if depth_class(limits[first]):
                    runs.append((first, index - 1))
                first = index
        return runs

    @staticmethod
    def _region_end(limits, start, stop, step, window):
        """Move a run end inward, up to window samples, to the deepest limit."""
        best = start
        for index in range(start + step, stop + step, step)[:window]:
            if limits[index] < limits[best] - 1e-3:
                best = index
        return best

    def _x_clear(self, tool_bounds):
        clearance = float(self.clearance)
        if not math.isfinite(clearance) or clearance < 0:
            raise ValueError("Clearance must be finite and non-negative")
        part_bounds = self.partSegmentGroup.boundbox()
        return max(self.stock.XMax, part_bounds.XMax) - tool_bounds.XMin + max(clearance, 0.01)

    def generateGCode(self):
        """Route plunges and inward finishing strokes with radial approach and retract."""
        path = Path()
        try:
            for segmentgroup in self.tool_paths:
                path.fromSegmentGroup(self, segmentgroup, protect_part=True,
                                      direction=RoutingDirection.RADIAL)
        except (ValueError, RuntimeError):
            self.tool_paths = []
            raise

        return path.commands
