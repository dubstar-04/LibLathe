"""Internal clearing and finishing; preparation and assembly fit remain user responsibilities."""

import math

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.op.base import BaseOP, CutDirection


class BoreOP(BaseOP):
    """Clear a bore in X or Z, then finish from bottom toward mouth."""

    @staticmethod
    def _reflect(group, radius):
        result = SegmentGroup()
        for edge in group.getSegments():
            result.addSegment(Segment(
                Point(radius - edge.start.X, edge.start.Z),
                Point(radius - edge.end.X, edge.end.Z), -edge.bulge))
        return result

    def generatePath(self):
        self.tool_paths = []
        self.clearing_paths = []
        if not isinstance(self.cut_direction, CutDirection):
            raise ValueError("Boring cut_direction must be a CutDirection enumeration member")
        edges = self.partSegmentGroup.getSegments()
        if not edges:
            raise ValueError("Boring requires a target bore contour")
        if self.tool is None or self.containment is None:
            raise ValueError("Boring requires an insert and tool-reference containment")
        if (isinstance(self.finish_passes, bool) or not isinstance(self.finish_passes, int)
                or self.finish_passes < 0):
            raise ValueError("finish_passes must be a non-negative integer")
        if not all(math.isfinite(value) for value in (
                self.pass_offset, self.stock_to_leave, self.clearance)):
            raise ValueError("Boring parameters must be finite")
        if self.pass_offset <= 0 or self.stock_to_leave < 0 or self.clearance <= 0:
            raise ValueError("Boring requires positive pass offset/clearance and non-negative allowance")
        limits = self.containment
        if (not all(math.isfinite(value) for value in (
                limits.XMin, limits.XMax, limits.ZMin, limits.ZMax))
                or limits.XMin < 0 or limits.XMin >= limits.XMax or limits.ZMin >= limits.ZMax):
            raise ValueError("Boring requires ordered non-negative radial and ordered axial limits")
        for index, edge in enumerate(edges):
            if (not all(math.isfinite(value) for value in (
                    edge.start.X, edge.start.Z, edge.end.X, edge.end.Z, edge.bulge))
                    or edge.Boundbox().XMin < 0 or edge.end.Z > edge.start.Z
                    or edge.getLength() <= 1e-6
                    or (index and not edges[index - 1].end.isSame(edge.start))):
                raise ValueError("Bore contour must be connected and run from mouth toward bottom")
        first, last = edges[0], edges[-1]
        if first.bulge or last.bulge or first.start.Z <= first.end.Z:
            raise ValueError("Boring prototype requires straight terminal edges and an axial mouth")
        if last.start.Z == last.end.Z and last.end.X >= last.start.X:
            raise ValueError("A terminal bore floor must run toward the axis")
        tool = self.tool.get_segmentgroup()
        if not tool.count():
            raise ValueError("Boring requires a non-empty insert outline")
        tool_bounds = tool.boundbox()
        allowance = self.stock_to_leave + max(0, self.finish_passes - 1) * self.pass_offset
        padding = (max(tool_bounds.XLength(), tool_bounds.ZLength())
                   + allowance + self.clearance + 1)
        extended = SegmentGroup()
        front = first.start.lerp(first.end, -padding / first.getLength())
        back = last.end.lerp(last.start, -padding / last.getLength())
        extended.addSegment(Segment(front, first.start))
        extended.extend(self.partSegmentGroup)
        extended.addSegment(Segment(last.end, back))
        # A translated radial reflection puts exterior bore material on the
        # axis side expected by the existing defeature/positive-offset pipeline.
        radius = max(extended.boundbox().XMax, limits.XMax) + padding
        material = self._reflect(extended, radius)
        insert = self._reflect(tool, 0)
        # Model finishing stays endpoint-trimmed; radial clearing starts at ZMax.
        x_min = limits.XMin
        if last.start.Z == last.end.Z:
            x_min = max(x_min, last.end.X - tool_bounds.XMax)
        z_min = max(limits.ZMin, last.end.Z - tool_bounds.ZMin)
        z_max = min(limits.ZMax, first.start.Z - tool_bounds.ZMin)
        if x_min >= limits.XMax or z_min >= z_max:
            return
        cutting_limits = BoundBox(Point(x_min, z_min), Point(limits.XMax, z_max))
        scan = BoundBox(Point(0, extended.boundbox().ZMin),
                        Point(radius + padding, extended.boundbox().ZMax))
        compensated = material.defeature(scan, insert, True)
        boundary = self._reflect(compensated.offset(allowance + 0.01, extend_start=True), radius)
        clearing = self._clearing_passes(boundary, cutting_limits, radius)
        paths = []
        for index in range(self.finish_passes):
            distance = self.stock_to_leave + (self.finish_passes - 1 - index) * self.pass_offset
            contour = compensated.offset(distance + 0.01, extend_start=True)
            for stroke in self._clip_path(self._reflect(contour, radius), cutting_limits):
                paths.append(stroke.reversed())
        # Certify geometric access against the complete target, not starting stock.
        # Preparation and bar/holder access are deliberately not inferred here.
        for index, group in enumerate(clearing + paths):
            edges = group.getSegments()
            start, end = edges[0].start, edges[-1].end
            position = Point(limits.XMin, self._front_clearance())
            transfers = []
            for _, point in self._approach(start, self.cut_direction == CutDirection.AXIAL and index < len(clearing)):
                transfers.append((position, point))
                position = point
            position = end
            for _, point in self._withdrawal(edges[-1]):
                transfers.append((position, point))
                position = point
            transfers.append((position, Point(limits.XMin, self._front_clearance())))
            for a, b in (*transfers, *((edge.start, edge.end) for edge in edges)):
                try:
                    material.validateToolSweep(
                        insert, Point(radius - a.X, a.Z), Point(radius - b.X, b.Z))
                except RuntimeError as error:
                    raise RuntimeError(
                        f"Boring target clearance failed for feed "
                        f"({a.X:.6f}, {a.Z:.6f}) -> ({b.X:.6f}, {b.Z:.6f}): {error}") from error
        self.clearing_paths = clearing
        self.tool_paths = paths

    def _clearing_passes(self, boundary, limits, radius):
        """Scan from the inner reference limit to the first allowance boundary."""
        reflected = self._reflect(boundary, radius)
        radial = self.cut_direction == CutDirection.RADIAL
        low, high = ((limits.ZMin, self.containment.ZMax) if radial else (limits.XMin, limits.XMax))
        count = max(1, math.ceil((high - low) / self.pass_offset))
        paths = []
        for index in range(count + 1):
            # The inner radius is the access lane, not an axial cut with no
            # room left for a perpendicular inward disengagement.
            if not radial and index == 0:
                continue
            position = high - (high - low) * index / count if radial else low + (high - low) * index / count
            # Continue the compensated mouth radius toward Start Depth without
            # exposing computational endpoint caps or altering finishing offsets.
            scan_z = min(position, limits.ZMax)
            start = Point(limits.XMin, scan_z) if radial else Point(position, limits.ZMax)
            end = Point(limits.XMax, scan_z) if radial else Point(position, limits.ZMin)
            if reflected.isInside(Point(radius - start.X, start.Z)):
                continue
            line = Segment(start, end)
            intersections = [point for edge in boundary.getSegments() for point in edge.intersect(line)
                             if point.distanceTo(start) > 1e-6]
            if intersections:
                end = min(intersections, key=lambda point: point.distanceTo(start))
                end = Point(end.X, start.Z) if radial else Point(start.X, end.Z)
            if radial:
                start, end = Point(start.X, position), Point(end.X, position)
            if start.distanceTo(end) > 1e-6:
                group = SegmentGroup()
                group.addSegment(Segment(start, end))
                paths.append(group)
        return paths

    def _front_clearance(self):
        return self.containment.ZMax + self.clearance

    def _approach(self, start, axial):
        limits = self.containment
        if axial:
            return [("G0", Point(start.X, self._front_clearance())),
                    ("G0", Point(start.X, limits.ZMax)), ("G1", start)]
        return [("G0", Point(limits.XMin, limits.ZMax)),
                ("G1", Point(limits.XMin, start.Z)), ("G1", start)]

    def _withdrawal(self, edge):
        end = edge.end
        limits = self.containment
        points = []
        if end.X > edge.start.X + 1e-6 and abs(end.Z - edge.start.Z) < 1e-5:
            lift = min(self.clearance, self.pass_offset, limits.ZMax - end.Z)
            if lift > 1e-5:
                end = Point(end.X, end.Z + lift)
                points.append(("G1", end))
            else:
                # At the front boundary, disengage axially into front
                # clearance before crossing back to the inner access lane.
                end = Point(end.X, self._front_clearance())
                points.append(("G0", end))
        points.append(("G1" if end.Z <= limits.ZMax else "G0",
                       Point(limits.XMin, end.Z)))
        return points

    def generateGCode(self):
        """Contain feeds and use rapid clearance transfers, without stock/access approval."""
        commands = [Command("G18")]
        groups = self.clearing_paths + self.tool_paths
        if not groups:
            return commands
        z_clear = self._front_clearance()
        x_clear = self.containment.XMin
        def feed(point):
            commands.append(Command("G1", {"X": point.X, "Z": point.Z, "F": self.hfeed}))

        def rapid(point):
            commands.append(Command("G0", {"X": point.X, "Z": point.Z, "F": self.hfeed}))

        commands.append(Command("G0", {"X": x_clear, "Z": z_clear, "F": self.hfeed}))
        for index, group in enumerate(groups):
            edges = group.getSegments()
            start, end = edges[0].start, edges[-1].end
            for movement, point in self._approach(
                    start, self.cut_direction == CutDirection.AXIAL and index < len(self.clearing_paths)):
                (feed if movement == "G1" else rapid)(point)
            for edge in edges:
                feed(edge.end)
            for movement, point in self._withdrawal(edges[-1]):
                (feed if movement == "G1" else rapid)(point)
            rapid(Point(x_clear, z_clear))
        return commands
