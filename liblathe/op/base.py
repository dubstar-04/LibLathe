from copy import copy
from enum import Enum

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.gcode.command import Command
from liblathe.gcode.path import Path
from liblathe.tool.tool import ToolSide
import math


class CutDirection(Enum):
    """Axis used for cutting passes."""
    RADIAL = "X"
    AXIAL = "Z"


def reflect_x_segments(segments):
    return [Segment(Point(-segment.start.X, segment.start.Z),
                    Point(-segment.end.X, segment.end.Z), -segment.bulge)
            for segment in segments]


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.containment = None
        self.stock = None
        self.tool = None
        self.partSegmentGroup = SegmentGroup()

        self.tool_paths = []
        self.clearing_paths = []

        self.allow_grooving = False
        self.cut_direction = CutDirection.RADIAL
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

        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
            else:
                raise Warning("Attempting to set undefined parameter '%s'" % param)

    def getParams(self):
        """Return operations parameters"""
        return {'allow_grooving': self.allow_grooving, 'pass_offset': self.pass_offset,
                'finish_passes': self.finish_passes, 'stock_to_leave': self.stock_to_leave, 'hfeed': self.hfeed,
                'vfeed': self.vfeed, 'clearance': self.clearance, 'cut_direction': self.cut_direction}

    def getGCode(self):
        """Base function for all turning operations"""

        if self.tool is None:
            raise Warning("Tool is unset")

        if self.stock is not None:
            if ((self.tool.side == ToolSide.FAR and self.stock.XMax > 1e-4)
                    or (self.tool.side == ToolSide.NEAR and self.stock.XMin < -1e-4)):
                self.tool_paths = []
                self.clearing_paths = []
                raise ValueError("Stock must use the tool side's signed radial coordinates")

        if self.tool.side == ToolSide.FAR:
            self.tool_paths = []
            self.clearing_paths = []
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
            planning.partSegmentGroup = SegmentGroup()
            for segment in reflect_x_segments(self.partSegmentGroup.getSegments()):
                planning.partSegmentGroup.addSegment(segment)
            planning.tool = copy(self.tool)
            planning.tool.segmentGroup = SegmentGroup()
            for segment in reflect_x_segments(self.tool.get_segmentgroup().getSegments()):
                planning.tool.segmentGroup.addSegment(segment)
            planning.tool.tool_rotation = 0
            planning.tool.side = ToolSide.NEAR
            planning.generatePath()
            commands = planning.generateGCode()
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
                    physical = SegmentGroup()
                    for segment in reflect_x_segments(group.getSegments()):
                        physical.addSegment(segment)
                    physical_paths.append(physical)
            return result

        self.generatePath()
        path = self.generateGCode()
        return path

    def generatePath(self):
        """Main processing function for each op"""
        pass

    def generateGCode(self):
        """Route contained passes from outermost to innermost."""
        path = Path()
        try:
            for group in reversed(self.tool_paths):
                path.fromSegmentGroup(self, group, protect_part=True, contain_feeds=True)
        except (ValueError, RuntimeError):
            self.tool_paths = []
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
