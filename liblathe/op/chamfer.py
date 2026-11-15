"""Equal-distance edge breaks on selected axial/radial profile corners."""

from copy import copy
from enum import Enum
import math

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.path import Path, RoutingDirection
from liblathe.op.base import BaseOP, Direction, MachiningMode


class ChamferPosition(Enum):
    FRONT = "Front"
    BACK = "Back"


class ChamferOP(BaseOP):
    def __init__(self):
        super().__init__()
        self.chamfer_size = 1.0
        self.pass_offset = 0.25
        self.corner_indices = ()
        self.direction = Direction.RADIAL
        self.chamfer_position = ChamferPosition.FRONT
        self._pass_parts = []

    def getParams(self):
        return {name: getattr(self, name) for name in (
            "chamfer_size", "chamfer_position", "corner_indices", "direction", "mode",
            "pass_offset", "hfeed", "vfeed", "clearance")}

    def _reset_paths(self):
        super()._reset_paths()
        self._pass_parts = []

    def _selected_corners(self, segments):
        if not segments:
            raise ValueError("Chamfering requires a part profile")
        if not isinstance(self.corner_indices, (tuple, list)):
            raise ValueError("Corner indices must be a list or tuple of profile vertex indices")
        indices = tuple(self.corner_indices)
        if not indices:
            raise ValueError("Select at least one corner for an edge break")
        if any(isinstance(index, bool) or not isinstance(index, int)
               or not 0 <= index <= len(segments) for index in indices):
            raise ValueError("Corner indices must identify profile vertices")
        if len(set(indices)) != len(indices):
            raise ValueError("Corner indices must be unique")
        return indices

    def _get_gcode(self):
        segments = self.partSegmentGroup.getSegments()
        for index in self._selected_corners(segments):
            corner = segments[index].start if index < len(segments) else segments[-1].end
            if abs(corner.X) <= 1e-6:
                raise ValueError("An edge break cannot be placed on the spindle axis")
        return super()._get_gcode()

    @staticmethod
    def _contact(tool, nx, nz):
        """Find the insert's supporting point, including circular nose extrema."""
        points = []
        for edge in tool.getSegments():
            points.extend((edge.start, edge.end))
            if edge.bulge:
                centre = edge.getCentrePoint()
                radius = edge.getRadius()
                candidate = Point(centre.X - nx * radius, centre.Z - nz * radius)
                if edge.pointOnSegment(candidate):
                    points.append(candidate)
        if not points:
            raise ValueError("Chamfering requires a non-empty insert outline")
        return min(points, key=lambda point: nx * point.X + nz * point.Z)

    @staticmethod
    def _part_with_breaks(segments, breaks):
        """Return the remaining contour after the specified breaks."""
        starts = [edge.start for edge in segments]
        ends = [edge.end for edge in segments]
        for index, chamfer in breaks.items():
            ends[index], starts[index + 1] = chamfer.start, chamfer.end
        part = SegmentGroup()
        for index, edge in enumerate(segments):
            if edge.getLength() > 1e-6:
                dx, dz = edge.end.X - edge.start.X, edge.end.Z - edge.start.Z
                if ((ends[index].X - starts[index].X) * dx
                        + (ends[index].Z - starts[index].Z) * dz <= 1e-6):
                    raise ValueError("Selected edge breaks overlap or consume an adjacent face")
                part.addSegment(Segment(starts[index], ends[index], edge.bulge))
            if index in breaks:
                part.addSegment(breaks[index])
        part.validate()
        return part

    def _pass_count(self, corner, chamfer):
        dx = chamfer.end.X - chamfer.start.X
        dz = chamfer.end.Z - chamfer.start.Z
        length = math.hypot(dx, dz)
        depth = ((corner.X - chamfer.start.X) * -dz
                 + (corner.Z - chamfer.start.Z) * dx) / length
        ratio = depth / self.pass_offset
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("Cannot advance chamfer pass at coordinate precision")
        count = max(1, math.ceil(ratio))
        if count > 1:
            for endpoint in (chamfer.start, chamfer.end):
                if (corner.lerp(endpoint, 1 / count).isSame(corner)
                        or corner.lerp(endpoint, 1 - 1 / count).isSame(endpoint)):
                    raise ValueError("Cannot advance chamfer pass at coordinate precision")
        return count

    def _compensated_pass(self, part, tool, start, end):
        """Compensate and certify a single pass against its remaining part."""
        dx, dz = end.X - start.X, end.Z - start.Z
        length = math.hypot(dx, dz)
        nx, nz = -dz / length, dx / length
        if self.inside_access and self.chamfer_position == ChamferPosition.BACK:
            nx, nz = -nx, -nz
        contact = self._contact(tool, nx, nz)
        # Keep tangency outside native floating-point boundary classification.
        shift = Point(-contact.X + nx * 0.0001, -contact.Z + nz * 0.0001)
        stroke = Segment(start.add(shift), end.add(shift))
        clipped = self._clip(stroke, self.containment.XMin, self.containment.XMax,
                             self.containment.ZMin, self.containment.ZMax)
        if (clipped is None or not clipped.start.isSame(stroke.start)
                or not clipped.end.isSame(stroke.end)):
            raise ValueError("Containment must include the complete compensated edge break")
        # BaseOP reflects internal radii, so decreasing planning X cuts outward in a bore.
        if stroke.end.X > stroke.start.X:
            stroke = Segment(stroke.end, stroke.start)
        # Bound each near-tangent proof's native subdivision work.
        spans = max(1, math.ceil(stroke.getLength() / (SegmentGroup.defeatureResolution / 10)))
        part.validateToolSweeps(tool, [
            (stroke.start.lerp(stroke.end, span / spans),
             stroke.start.lerp(stroke.end, (span + 1) / spans))
            for span in range(spans)])
        group = SegmentGroup()
        group.addSegment(stroke)
        return group

    def generatePath(self):
        self._begin_generation(pass_offset=True)
        if not math.isfinite(self.chamfer_size) or self.chamfer_size <= 0:
            raise ValueError("chamfer_size must be finite and positive")
        if self.direction != Direction.RADIAL:
            raise ValueError("Chamfer machining direction must be radial")
        if not isinstance(self.chamfer_position, ChamferPosition):
            raise ValueError("Chamfer position must be a ChamferPosition enumeration member")
        original = self.partSegmentGroup.getSegments()
        indices = self._selected_corners(original)
        if self.inside_access:
            def close_profile(profile):
                return [
                    Segment(Point(0, profile[0].start.Z), profile[0].start),
                    *profile,
                    Segment(profile[-1].end, Point(0, profile[-1].end.Z)),
                ]

            segments = close_profile(original)
            turns = []
            for index in indices:
                incoming, outgoing = segments[index:index + 2]
                dx, dz = incoming.end.X - incoming.start.X, incoming.end.Z - incoming.start.Z
                ex, ez = outgoing.end.X - outgoing.start.X, outgoing.end.Z - outgoing.start.Z
                turns.append(dx * ez - dz * ex)
            if all(turn > 1e-6 for turn in turns):
                original = [Segment(edge.end, edge.start, -edge.bulge)
                            for edge in reversed(original)]
                indices = tuple(len(original) - index for index in indices)
            elif any(turn > 1e-6 for turn in turns):
                raise ValueError("Selected internal edge breaks must have consistent profile winding")
        # Open profiles close radially to the axis. This also supplies the bore mouth
        # face in BaseOP's reflected internal planning frame.
        segments = [Segment(Point(0, original[0].start.Z), original[0].start),
                    *original,
                    Segment(original[-1].end, Point(0, original[-1].end.Z))]
        breaks = {}
        for index in sorted(indices):
            incoming, outgoing = segments[index:index + 2]
            dx, dz = incoming.end.X - incoming.start.X, incoming.end.Z - incoming.start.Z
            ex, ez = outgoing.end.X - outgoing.start.X, outgoing.end.Z - outgoing.start.Z
            if (not incoming.end.isSame(outgoing.start)
                    or incoming.bulge or outgoing.bulge
                    or not ((abs(dx) <= 1e-6 and abs(ez) <= 1e-6)
                            or (abs(dz) <= 1e-6 and abs(ex) <= 1e-6))
                    or dx * ez - dz * ex >= -1e-6):
                raise ValueError("Edge breaks require convex axial/radial right-angle corners")
            size = self.chamfer_size
            if min(incoming.getLength(), outgoing.getLength()) <= size + 1e-6:
                raise ValueError("Chamfer size must be smaller than both adjacent faces")
            corner = incoming.end
            start = corner.lerp(incoming.start, size / incoming.getLength())
            end = corner.lerp(outgoing.end, size / outgoing.getLength())
            if start.isSame(end):
                raise ValueError("Chamfer size cannot be represented at coordinate precision")
            breaks[index] = Segment(start, end)

        finished = self._part_with_breaks(segments, breaks)

        tool = self.tool.get_segmentgroup()
        paths = []
        parts = []
        completed = {}
        for index, chamfer in breaks.items():
            corner = segments[index].end
            count = self._pass_count(corner, chamfer)
            previous_start, previous_end = corner, corner
            for pass_index in range(1, count + 1):
                fraction = pass_index / count
                start = corner.lerp(chamfer.start, fraction)
                end = corner.lerp(chamfer.end, fraction)
                if start.isSame(previous_start) or end.isSame(previous_end):
                    raise ValueError("Cannot advance chamfer pass at coordinate precision")
                previous_start, previous_end = start, end
                completed[index] = Segment(start, end)
                part = (finished if pass_index == count and len(completed) == len(breaks)
                        else self._part_with_breaks(segments, completed))
                paths.append(self._compensated_pass(part, tool, start, end))
                parts.append(part)
        self.tool_paths = paths
        self._pass_parts = parts

    def generateGCode(self):
        if not self.tool_paths or len(self.tool_paths) != len(self._pass_parts):
            self._reset_paths()
            raise ValueError("Generate chamfer paths before requesting G-code")
        planning = copy(self)
        if not self.inside_access:
            tool_bounds = self.tool.get_segmentgroup().boundbox()
            radial_max = max(
                self.partSegmentGroup.boundbox().XMax - tool_bounds.XMin,
                max(group.boundbox().XMax for group in self.tool_paths))
            if self.stock is not None:
                radial_max = max(radial_max, self.stock.XMax - tool_bounds.XMin)
            # Compensation containment is not an approach boundary.
            planning.containment = BoundBox(
                Point(self.containment.XMin, self.containment.ZMin),
                Point(min(self.containment.XMax, radial_max + 0.0001),
                      self.containment.ZMax))
        direction = RoutingDirection.RADIAL
        path = Path()
        try:
            for index, (group, part) in enumerate(zip(self.tool_paths, self._pass_parts)):
                planning.partSegmentGroup = part
                path.fromSegmentGroup(
                    planning, group, protect_part=True, direction=direction,
                    return_to_clearance=(direction == RoutingDirection.RADIAL
                                         and self.inside_access and index == len(self.tool_paths) - 1),
                    inside_access=self.inside_access)
        except (ValueError, RuntimeError):
            self._reset_paths()
            raise
        return path.commands
