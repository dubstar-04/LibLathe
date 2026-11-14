from copy import copy
from enum import Enum

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.gcode.command import Command, optimise_rapids
from liblathe.gcode.path import Path, RoutingDirection
from liblathe.tool.tool import ToolSide
import math


class MachiningMode(Enum):
    EXTERNAL = "External"
    INTERNAL = "Internal"


class Direction(Enum):
    """Cutting direction shared by Rough and Profile."""
    NEGATIVE_Z = "-Z"
    POSITIVE_Z = "+Z"
    RADIAL = "Radial"


def reflect_x_segments(segments):
    group = SegmentGroup()
    for segment in segments:
        group.addSegment(segment)
    return group.reflectX().getSegments()


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.containment = None
        self.stock = None
        self.tool = None
        self.partSegmentGroup = SegmentGroup()
        self.mode = MachiningMode.EXTERNAL
        self.inside_access = False

        self.tool_paths = []
        self.clearing_paths = []

        self.allow_grooving = False
        self.pass_offset = 1.5
        self.finish_passes = 1
        self.stock_to_leave = 0
        self.hfeed = 100
        self.vfeed = 50
        self.clearance = 3

        self.leadin_angle = math.pi * 1.5
        self.leadout_angle = math.pi * 1.75

    def setParams(self, params):
        """Set operations parameters"""

        supported = self.getParams().keys() | {"leadin_angle", "leadout_angle"}
        for param in params:
            if param not in supported:
                raise Warning("Attempting to set undefined parameter '%s'" % param)
        for param, value in params.items():
            setattr(self, param, value)

    def getParams(self):
        """Return operations parameters"""
        return {'allow_grooving': self.allow_grooving, 'pass_offset': self.pass_offset,
                'finish_passes': self.finish_passes, 'stock_to_leave': self.stock_to_leave, 'hfeed': self.hfeed,
                'vfeed': self.vfeed, 'clearance': self.clearance}

    def getGCode(self):
        """Base function for all turning operations"""

        self._reset_paths()
        try:
            return optimise_rapids(self._get_gcode())
        except (ValueError, RuntimeError, Warning):
            self._reset_paths()
            raise

    def _get_gcode(self):
        if self.tool is None:
            raise Warning("Tool is unset")
        if not isinstance(self.mode, MachiningMode):
            raise ValueError("Mode must be a MachiningMode enumeration member")

        if self.stock is not None:
            if ((self.tool.side == ToolSide.FAR and self.stock.XMax > 1e-4)
                    or (self.tool.side == ToolSide.NEAR and self.stock.XMin < -1e-4)):
                raise ValueError("Stock must use the tool side's signed radial coordinates")

        if self.tool.side == ToolSide.FAR:
            if self.containment is None or self.containment.XMax > 1e-4 or self.containment.XMin >= 0:
                raise ValueError("Far-side containment must use negative X coordinates")
            if self.partSegmentGroup.boundbox().XMax > 1e-4:
                raise ValueError("Far-side part geometry must use negative X coordinates")
            planning = copy(self)
            planning.tool_paths = []
            planning.clearing_paths = []
            planning.containment = BoundBox(Point(-self.containment.XMax, self.containment.ZMin),
                                      Point(-self.containment.XMin, self.containment.ZMax))
            if self.stock is not None:
                planning.stock = BoundBox(
                    Point(-self.stock.XMax, self.stock.ZMin),
                    Point(-self.stock.XMin, self.stock.ZMax))
            planning.partSegmentGroup = self.partSegmentGroup.reflectX()
            planning.tool = copy(self.tool)
            planning.tool.segmentGroup = self.tool.get_segmentgroup().reflectX()
            planning.tool.tool_rotation = 0
            planning.tool.side = ToolSide.NEAR
            commands = planning._get_gcode()
            result = []
            for command in commands:
                parameters = dict(command.getParams())
                for name in ("X", "I"):
                    if name in parameters:
                        parameters[name] = -parameters[name]
                movement = {"G2": "G3", "G3": "G2", "G02": "G03", "G03": "G02"}.get(
                    command.get_movement(), command.get_movement())
                result.append(Command(movement, parameters))
            for name in ("tool_paths", "clearing_paths"):
                physical_paths = getattr(self, name)
                for group in getattr(planning, name):
                    physical_paths.append(group.reflectX())
            return result

        if self.mode == MachiningMode.INTERNAL:
            return self._get_internal_gcode()

        self.generatePath()
        path = self.generateGCode()
        return path

    def _get_internal_gcode(self):
        if self.containment is None:
            raise ValueError("Internal machining requires explicit containment")
        limits = self.containment
        if limits.XMin < -1e-4 or limits.XMin >= limits.XMax:
            raise ValueError("Internal containment must have ordered non-negative radii")
        if self.partSegmentGroup.count() and self.partSegmentGroup.boundbox().XMin < -1e-4:
            raise ValueError("Internal part geometry must use non-negative radii")

        tool = self.tool.get_segmentgroup()
        tool_bounds = tool.boundbox()
        clearance = float(self.clearance)
        if not math.isfinite(clearance) or clearance < 0:
            raise ValueError("Clearance must be finite and non-negative")
        radial_max = max(limits.XMax, self.partSegmentGroup.boundbox().XMax)
        if self.stock is not None:
            radial_max = max(radial_max, self.stock.XMax)
        frame_radius = (radial_max + max(tool_bounds.XLength(), tool_bounds.ZLength())
                        + max(clearance, 0.01) + 1)
        if not math.isfinite(frame_radius):
            raise ValueError("Internal frame radius must be finite")

        planning = copy(self)
        planning.inside_access = True
        planning.tool_paths = []
        planning.clearing_paths = []
        planning.containment = BoundBox(
            Point(frame_radius - limits.XMax, limits.ZMin),
            Point(frame_radius - limits.XMin, limits.ZMax))
        planning.partSegmentGroup = self.partSegmentGroup.reflectX(frame_radius)
        if self.stock is not None:
            planning.stock = BoundBox(
                Point(frame_radius - self.stock.XMax, self.stock.ZMin),
                Point(frame_radius - self.stock.XMin, self.stock.ZMax))
        planning.tool = copy(self.tool)
        planning.tool.segmentGroup = tool.reflectX()
        planning.tool.tool_rotation = 0
        planning.generatePath()
        commands = planning.generateGCode()

        result = []
        for command in commands:
            parameters = dict(command.getParams())
            if "X" in parameters:
                parameters["X"] = frame_radius - parameters["X"]
            if "I" in parameters:
                parameters["I"] = -parameters["I"]
            movement = {"G2": "G3", "G3": "G2", "G02": "G03", "G03": "G02"}.get(
                command.get_movement(), command.get_movement())
            result.append(Command(movement, parameters))
        for name in ("tool_paths", "clearing_paths"):
            setattr(self, name, [group.reflectX(frame_radius)
                                 for group in getattr(planning, name)])
        return result

    def generatePath(self):
        """Main processing function for each op"""
        pass

    def _reset_paths(self):
        self.tool_paths = []
        self.clearing_paths = []

    def _begin_generation(self, *, pass_offset=False, finish_passes=False, allowance=False):
        """Clear published paths and validate only the parameters this strategy uses."""
        self._reset_paths()
        if not isinstance(self.mode, MachiningMode):
            raise ValueError("Mode must be a MachiningMode enumeration member")
        if self.tool is None or self.containment is None:
            raise ValueError("Operation requires a tool and explicit containment")
        limits = self.containment
        if (not all(math.isfinite(value) for value in (
                limits.XMin, limits.XMax, limits.ZMin, limits.ZMax))
                or limits.XMin > limits.XMax or limits.ZMin >= limits.ZMax):
            raise ValueError("Containment must have finite, ordered radial and axial limits")
        if not math.isfinite(self.clearance) or self.clearance < 0:
            raise ValueError("Clearance must be finite and non-negative")
        self._validate_parameters(pass_offset=pass_offset, finish_passes=finish_passes, allowance=allowance)

    def _validate_parameters(self, *, pass_offset=False, finish_passes=False, allowance=False):
        if pass_offset and (not math.isfinite(self.pass_offset) or self.pass_offset <= 0):
            raise ValueError("pass_offset must be finite and positive")
        if finish_passes and (
                isinstance(self.finish_passes, bool) or not isinstance(self.finish_passes, int)
                or self.finish_passes < 0):
            raise ValueError("finish_passes must be a non-negative integer")
        if allowance and (not math.isfinite(self.stock_to_leave) or self.stock_to_leave < 0):
            raise ValueError("stock_to_leave must be finite and non-negative")

    @staticmethod
    def _stations(low, high, step, *, include_end=False):
        """Retain fixed-increment grids, rejecting increments lost to rounding."""
        position = low
        while position < high or (include_end and position == high):
            yield position
            if position == high:
                return
            following = position + step
            next_native = Point(following, 0).X
            if (not math.isfinite(next_native) or following <= position
                    or next_native <= Point(position, 0).X):
                raise ValueError("Cannot advance cutting station at coordinate precision")
            position = following

    @staticmethod
    def _stations_descending(high, low, max_step):
        """Return evenly spaced high-to-low stations with no gap over max_step."""
        if not all(math.isfinite(value) for value in (high, low, max_step)) or max_step <= 0:
            raise ValueError("Station bounds must be finite and max_step must be positive")
        distance = high - low
        if distance < -1e-6:
            raise ValueError("Descending station bounds must be ordered high to low")
        if distance <= 1e-6:
            return [high]
        count = max(1, math.ceil(distance / max_step - 1e-9))
        increment = distance / count

        def native(station):
            return Point(0, station).Z

        # Native spacing is coarsest at an end of the range, so reject an increment
        # lost there before allocating a grid that could never be represented.
        if (native(high - increment) >= native(high)
                or native(low + increment) <= native(low)):
            raise ValueError("Cannot advance axial station at coordinate precision")
        stations = [high]
        for index in range(1, count + 1):
            station = low if index == count else high - index * increment
            if native(station) >= native(stations[-1]):
                raise ValueError("Cannot advance axial station at coordinate precision")
            stations.append(station)
        return stations

    def _defeature_profile(self, allow_grooving):
        """Return the simplified tool-accessible contour."""
        return self._defeature_profile_with_samples(allow_grooving).contour

    def _defeature_profile_with_samples(self, allow_grooving):
        """Return scan samples and contour without shortening the contact-space scan."""
        tool = self.tool.get_segmentgroup()
        contact = tool.getRadialContactPoint()
        # Native defeature subtracts contact.Z and excludes its lower endpoint.
        scan_min = self.containment.ZMin + min(0, contact.Z) - 2 * SegmentGroup.defeatureResolution
        scan = BoundBox(Point(self.containment.XMin, scan_min),
                        Point(self.containment.XMax, self.containment.ZMax))
        return self.partSegmentGroup.defeatureWithSamples(scan, tool, allow_grooving)

    def generateGCode(self):
        """Route contained passes from outermost to innermost."""
        return self._route_paths(reversed(self.tool_paths))

    def _grooving_clearance(self):
        """Return the radial lane just above the containment for external grooving, else None."""
        if not self.allow_grooving or self.inside_access:
            return None
        tool_bounds = self.tool.get_segmentgroup().boundbox()
        return self.containment.XMax + max(0.0, -tool_bounds.XMin) + max(self.clearance, 0.01)

    def _route_paths(self, groups, *, protect_part=True, direction=RoutingDirection.AUTO,
                     radial_clearance=None):
        """Route ordered groups without choosing the operation's machining policy."""
        path = Path()
        groups = tuple(groups)
        # radial routes end at their lane beside the last pass, so leave the work for the next op
        returns = direction == RoutingDirection.RADIAL and (
            radial_clearance is not None or self.inside_access)
        try:
            for index, group in enumerate(groups):
                path.fromSegmentGroup(
                    self, group, protect_part=protect_part, direction=direction,
                    radial_clearance=radial_clearance,
                    return_to_clearance=returns and index == len(groups) - 1,
                    inside_access=self.inside_access)
        except (ValueError, RuntimeError):
            self._reset_paths()
            raise
        return path.commands

    def _add_lead(self, group, anchor, angle, limits, *, lead_in=False):
        """Shorten a lead along its original direction to fit the cutting limits."""
        end = anchor.project(angle, self.pass_offset)
        fraction = 1.0
        for start, delta, low, high in (
                (anchor.X, end.X - anchor.X, limits.XMin, limits.XMax),
                (anchor.Z, end.Z - anchor.Z, limits.ZMin, limits.ZMax)):
            if delta > 0:
                fraction = min(fraction, (high - start) / delta)
            elif delta < 0:
                fraction = min(fraction, (low - start) / delta)
        if fraction <= 1e-6:
            return
        end = anchor.lerp(end, fraction)
        if anchor.distanceTo(end) <= 1e-6:
            return
        start, end = (end, anchor) if lead_in else (anchor, end)
        self.partSegmentGroup.validateToolSweep(self.tool.get_segmentgroup(), start, end)
        group.addSegment(Segment(start, end))

    @staticmethod
    def _clip(segment, x_min, x_max, z_low, z_high):
        """Return the part of a line segment inside the X and Z limits, or None."""
        if segment.bulge != 0:
            raise ValueError("Containment clipping requires line segments")
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

    def _clip_path(self, group, limits=None):
        """Clip an offset polyline, keeping disconnected strokes separate."""
        if limits is None:
            limits = self.containment
        strokes = []
        stroke = SegmentGroup()
        previous = None
        for segment in group.getSegments():
            clipped = self._clip(segment, limits.XMin, limits.XMax, limits.ZMin, limits.ZMax)
            if clipped is None or (previous is not None and not previous.end.isSame(clipped.start)):
                if stroke.count():
                    strokes.append(stroke)
                    stroke = SegmentGroup()
            if clipped is not None:
                stroke.addSegment(clipped)
            previous = clipped
        if stroke.count():
            strokes.append(stroke)
        return strokes

    @staticmethod
    def _inward_strokes(contour):
        """Split a contour at gaps and radial reversals, orienting each run inward."""
        strokes = []
        run = SegmentGroup()
        direction = 0
        previous = None
        for segment in contour.getSegments():
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

    def addPartSegments(self, partSegments):
        """Add edges to define the part geometry partSegments = array of LibLathe segments"""

        for segment in partSegments:
            self.partSegmentGroup.addSegment(segment)

        self.partSegmentGroup.validate()
        # self.partSegmentGroup.create_freecad_shape('partSegmentGroup')

    def add_containment(self, bounds):
        """Set the operation's machining limits as a LibLathe BoundBox."""
        self.containment = bounds

    def add_containment_from_limits(self, xmin, xmax, zmin, zmax):
        """Set the operation's radial and axial machining limits."""
        self.add_containment(BoundBox(Point(xmin, zmin), Point(xmax, zmax)))

    def add_stock(self, bounds):
        """Set the physical stock envelope used for safe clearance routing."""
        values = (bounds.XMin, bounds.XMax, bounds.ZMin, bounds.ZMax)
        if (not all(math.isfinite(value) for value in values)
                or bounds.XMax <= bounds.XMin or bounds.ZMax <= bounds.ZMin):
            raise ValueError("Stock must have finite bounds and positive radial/axial extents")
        self.stock = bounds

    def add_tool(self, tool):
        """Set the tool for the operation"""
        self.tool = tool
