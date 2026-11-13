"""Straight single-start external threading with spindle-synchronized G33 passes."""

import math
from numbers import Real

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.op.base import BaseOP


class ThreadOP(BaseOP):
    def __init__(self):
        super().__init__()
        self.pitch = None
        self.pass_offset = 0.1
        self.spring_passes = 0

    def getParams(self):
        return {"pitch": self.pitch, "pass_offset": self.pass_offset,
                "spring_passes": self.spring_passes, "clearance": self.clearance}

    def generatePath(self):
        self._begin_generation(pass_offset=True)
        if (isinstance(self.pitch, bool) or not isinstance(self.pitch, Real)
                or not math.isfinite(self.pitch) or self.pitch <= 0):
            raise ValueError("Thread pitch must be finite and positive")
        if (isinstance(self.spring_passes, bool) or not isinstance(self.spring_passes, int)
                or self.spring_passes < 0):
            raise ValueError("spring_passes must be a non-negative integer")
        if isinstance(self.pass_offset, bool):
            raise ValueError("pass_offset must be finite and positive")
        if self.clearance <= 0:
            raise ValueError("Threading clearance must be positive")
        limits = self.containment
        if not 0 < limits.XMin < limits.XMax:
            raise ValueError("External threading requires positive root and crest radii with nonzero depth")
        if not self.partSegmentGroup.count():
            raise ValueError("Threading requires a part profile for entry and withdrawal checks")

        tool = self.tool.get_segmentgroup()
        outside = self._clearance_point(tool.boundbox())
        # Entry is checked against the uncut part, so ZMax needs run-in clearance.
        try:
            self.partSegmentGroup.validateToolSweeps(tool, [
                (outside, Point(outside.X, limits.ZMax)),
                (Point(outside.X, limits.ZMax), Point(limits.XMin, limits.ZMax)),
            ])
        except RuntimeError as error:
            raise RuntimeError(f"Threading entry needs run-in clearance beyond the +Z limit: {error}") from error
        # The passes remove the thread band, so the deepest pass and withdrawal only
        # need to clear material outside it (e.g. a shoulder without run-out relief).
        try:
            self._threaded_part().validateToolSweeps(tool, [
                (Point(limits.XMin, limits.ZMax), Point(limits.XMin, limits.ZMin)),
                (Point(limits.XMin, limits.ZMin), Point(outside.X, limits.ZMin)),
                (Point(outside.X, limits.ZMin), outside),
            ])
        except RuntimeError as error:
            raise RuntimeError(
                f"Threading pass or withdrawal collides with the part outside the thread band; "
                f"check run-out relief beyond the -Z limit: {error}") from error
        # Withdrawal and plunge at the lane are covered above; only the return traverse is new.
        lane = self._local_clearance(tool.boundbox())
        try:
            self.partSegmentGroup.validateToolSweeps(tool, [
                (Point(lane, limits.ZMin), Point(lane, limits.ZMax)),
            ])
        except RuntimeError as error:
            raise RuntimeError(
                f"Threading return above the containment collides with the part: {error}") from error

        radii = []
        radius = limits.XMax
        while radius > limits.XMin:
            following = Point(max(limits.XMin, radius - self.pass_offset), limits.ZMax).X
            if not math.isfinite(following) or following >= radius:
                raise ValueError("Cannot advance threading pass at coordinate precision")
            radii.append(following)
            radius = following
        radii.extend([limits.XMin] * self.spring_passes)
        paths = []
        for radius in radii:
            group = SegmentGroup()
            group.addSegment(Segment(Point(radius, limits.ZMax), Point(radius, limits.ZMin)))
            paths.append(group)
        self.tool_paths = paths

    def _threaded_part(self):
        """Return the part profile with the containment thread band removed.

        The band extends just below the root so the insert tip is not certified
        against a boundary it touches by construction.
        """
        limits = self.containment
        root = limits.XMin - min(0.01, limits.XMin / 2)
        result = SegmentGroup()
        previous = None
        for segment in self.partSegmentGroup.getSegments():
            for start, end, bulge, inside in self._band_pieces(segment, root):
                if inside:
                    start, end, bulge = Point(root, start.Z), Point(root, end.Z), 0
                if previous is not None and not previous.isSame(start):
                    result.addSegment(Segment(previous, start))
                if not start.isSame(end):
                    result.addSegment(Segment(start, end, bulge))
                previous = end
        return result

    def _band_pieces(self, segment, root):
        """Split a segment at the band edges, flagging pieces inside the band."""
        limits = self.containment
        start, end, bulge = segment.start, segment.end, segment.bulge
        if bulge == 0:
            def at(t):
                return Point(start.X + t * (end.X - start.X), start.Z + t * (end.Z - start.Z))
            cuts = []
            for low, high, value in ((start.Z, end.Z, limits.ZMin), (start.Z, end.Z, limits.ZMax),
                                     (start.X, end.X, root)):
                if high != low:
                    cuts.append((value - low) / (high - low))
        else:
            centre, radius = segment.getCentrePoint(), segment.getRadius()
            first = math.atan2(start.Z - centre.Z, start.X - centre.X)
            last = math.atan2(end.Z - centre.Z, end.X - centre.X)
            sweep = 4 * math.atan(abs(bulge))
            # Orient the sweep to whichever direction reaches the end point.
            forward = (last - first) % (2 * math.pi)
            direction = 1 if abs(forward - sweep) <= abs((2 * math.pi - forward) - sweep) else -1

            def at(t):
                angle = first + direction * sweep * t
                return Point(centre.X + radius * math.cos(angle), centre.Z + radius * math.sin(angle))

            angles = []
            for value in (limits.ZMin, limits.ZMax):
                ratio = (value - centre.Z) / radius
                if -1 <= ratio <= 1:
                    angles.extend((math.asin(ratio), math.pi - math.asin(ratio)))
            ratio = (root - centre.X) / radius
            if -1 <= ratio <= 1:
                angles.extend((math.acos(ratio), -math.acos(ratio)))
            cuts = [((direction * (angle - first)) % (2 * math.pi)) / sweep for angle in angles]
        params = [0.0, *sorted(t for t in cuts if 1e-9 < t < 1 - 1e-9), 1.0]
        pieces = []
        for t0, t1 in zip(params, params[1:]):
            middle = at((t0 + t1) / 2)
            inside = middle.X > root and limits.ZMin <= middle.Z <= limits.ZMax
            piece_start = start if t0 == 0 else at(t0)
            piece_end = end if t1 == 1 else at(t1)
            piece_bulge = 0 if bulge == 0 else math.copysign(math.tan((t1 - t0) * sweep / 4), bulge)
            pieces.append((piece_start, piece_end, piece_bulge, inside))
        return pieces

    def _clearance_point(self, tool_bounds):
        limits = self.containment
        part = self.partSegmentGroup.boundbox()
        x_limit = max(limits.XMax, limits.XMax - tool_bounds.XMin,
                      part.XMax - tool_bounds.XMin)
        z_limit = max(limits.ZMax, limits.ZMax - tool_bounds.ZMin,
                      part.ZMax - tool_bounds.ZMin)
        if self.stock is not None:
            x_limit = max(x_limit, self.stock.XMax - tool_bounds.XMin)
            z_limit = max(z_limit, self.stock.ZMax - tool_bounds.ZMin)
        outside = Point(x_limit + self.clearance, z_limit + self.clearance)
        if (not all(math.isfinite(value) for value in (outside.X, outside.Z))
                or outside.X <= x_limit or outside.Z <= z_limit):
            raise ValueError("Cannot represent threading clearance at coordinate precision")
        return outside

    def _local_clearance(self, tool_bounds):
        """Return the radius where the tool clears the containment crest by the clearance."""
        lane = self.containment.XMax - tool_bounds.XMin + self.clearance
        if not math.isfinite(lane) or lane <= self.containment.XMax - tool_bounds.XMin:
            raise ValueError("Cannot represent threading clearance at coordinate precision")
        return lane

    def generateGCode(self):
        """Enter and leave via the global clearance; reposition between passes just above the crest."""
        if not self.tool_paths:
            raise ValueError("Generate threading paths before requesting G-code")
        tool_bounds = self.tool.get_segmentgroup().boundbox()
        outside = self._clearance_point(tool_bounds)
        lane = self._local_clearance(tool_bounds)
        limits = self.containment
        commands = [Command("G18"), Command("G90"), Command("G8"),
                    Command("G0", {"X": outside.X, "Z": outside.Z}),
                    Command("G0", {"X": outside.X, "Z": limits.ZMax}),
                    Command("G0", {"X": lane, "Z": limits.ZMax})]
        for index, group in enumerate(self.tool_paths):
            segment = group.getSegments()[0]
            start, end = segment.start, segment.end
            if index:
                commands.append(Command("G0", {"X": lane, "Z": start.Z}))
            commands.extend([
                Command("G0", {"X": start.X, "Z": start.Z}),
                Command("G33", {"X": end.X, "Z": end.Z, "K": self.pitch}),
                Command("G0", {"X": lane, "Z": end.Z}),
            ])
        commands.extend([Command("G0", {"X": outside.X, "Z": limits.ZMin}),
                         Command("G0", {"X": outside.X, "Z": outside.Z})])
        return commands
