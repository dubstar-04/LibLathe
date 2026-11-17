import math

import liblathe.op.base
from liblathe.op.base import RetractMode
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.command import Command
from liblathe.gcode.path import RoutingDirection

TOLERANCE = 1e-5
MAX_PECKS = 10000


class PartoffOP(liblathe.op.base.BaseOP):

    def __init__(self):
        super().__init__()
        self.peck_depth = 0.0
        self.retract_mode = RetractMode.FULL_RETRACT
        self.reentry_gap_widths = 1.0
        self.chip_break_retract_widths = 1.0
        self.outline_margin = 0.0

    @property
    def preserve_rapid_reversals(self):
        """Keep the out-and-back rapids of full retracts."""
        return bool(self.peck_depth) and self.retract_mode == RetractMode.FULL_RETRACT

    def getParams(self):
        return {
            **super().getParams(),
            "peck_depth": self.peck_depth,
            "retract_mode": self.retract_mode,
            "reentry_gap_widths": self.reentry_gap_widths,
            "chip_break_retract_widths": self.chip_break_retract_widths,
            "outline_margin": self.outline_margin,
        }

    def generatePath(self):
        """Generate the path for the Part operation"""

        self._begin_generation()
        limits = self.containment
        face = limits.ZMax
        tool_bounds = self.tool.get_segmentgroup().boundbox()

        if not math.isfinite(self.outline_margin) or self.outline_margin < 0:
            raise ValueError("Outline margin must be finite and non-negative")
        # An approximated outline may extend past the model's back face by its margin.
        if (self.partSegmentGroup.count()
                and self.partSegmentGroup.boundbox().ZMin < face - self.outline_margin - TOLERANCE):
            raise ValueError("Parting face (containment maximum Z) must not be inside the part")
        if limits.ZLength() < tool_bounds.ZLength() - TOLERANCE:
            raise ValueError("Parting containment must be at least as wide as the tool")

        if not tool_bounds.ZMin - TOLERANCE <= 0 <= tool_bounds.ZMax + TOLERANCE:
            raise ValueError("Tool reference must lie within the tool's axial extent")
        # Place the tool's +Z edge on the face so the whole tool stays on the stock side.
        z = face - tool_bounds.ZMax
        self._validate_pecking(limits.XLength(), tool_bounds.ZLength())

        segmentgroup = SegmentGroup()
        segmentgroup.addSegment(Segment(Point(limits.XMax, z), Point(limits.XMin, z)))
        self.tool_paths.append(segmentgroup)

    def _validate_pecking(self, depth, width):
        if not math.isfinite(self.peck_depth) or self.peck_depth < 0:
            raise ValueError("Peck depth must be finite and non-negative")
        if not isinstance(self.retract_mode, RetractMode):
            raise ValueError("Retract mode must be a RetractMode enumeration member")
        if not self.peck_depth:
            return
        gap = self._peck_gap() * width
        if not math.isfinite(gap) or gap <= 0:
            raise ValueError("Peck re-entry gap / chip-break retract must be finite and positive")
        if depth / self.peck_depth > MAX_PECKS:
            raise ValueError("Peck depth would need more than {} pecks".format(MAX_PECKS))

    def _peck_gap(self):
        """Return the gap above the last peck, in tool widths, for the retract mode."""
        return (self.reentry_gap_widths if self.retract_mode == RetractMode.FULL_RETRACT
                else self.chip_break_retract_widths)

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        commands = self._route_paths(self.tool_paths, protect_part=False, direction=RoutingDirection.RADIAL)
        if not self.peck_depth:
            return commands
        return self._peck(commands, self.tool_paths[0].getSegments()[0])

    def _peck(self, commands, cut):
        """Split the parting feed into pecks.

        Partial retracts back off by the gap to break the chip; full retracts leave
        the cut at its start radius, then rapid back to the gap above the last peck.
        """
        index = next(i for i, command in enumerate(commands)
                     if command.get_movement() == "G1"
                     and abs(command.getParams()["X"] - cut.end.X) <= TOLERANCE
                     and abs(command.getParams()["Z"] - cut.end.Z) <= TOLERANCE)
        feed = commands[index].getParams()["F"]
        gap = self._peck_gap() * self.tool.get_segmentgroup().boundbox().ZLength()
        stations = self._stations_descending(cut.start.X, cut.end.X, self.peck_depth)[1:]
        pecks = []
        for station in stations[:-1]:
            pecks.append(Command("G1", {"X": station, "Z": cut.end.Z, "F": feed}))
            if self.retract_mode == RetractMode.FULL_RETRACT:
                pecks.append(Command("G0", {"X": cut.start.X, "Z": cut.end.Z}))
            pecks.append(Command("G0", {"X": min(cut.start.X, station + gap), "Z": cut.end.Z}))
        pecks.append(commands[index])
        return commands[:index] + pecks + commands[index + 1:]
