"""Centreline drilling with explicit pecks and optional drill-tip compensation."""

import math
from enum import Enum

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.op.base import BaseOP
from liblathe.tool.drill import Drill


MAX_PECKS = 10000


class RetractMode(Enum):
    PARTIAL_RETRACT = "Partial Retract"
    FULL_RETRACT = "Full Retract"


class DrillOP(BaseOP):
    preserve_rapid_reversals = True

    def __init__(self):
        super().__init__()
        self.peck_depth = 0.0
        self.retract_mode = RetractMode.FULL_RETRACT
        self.reentry_gap_diameters = 1.0
        self.chip_break_retract_diameters = 1.0
        self.tip_compensation = False

    def getParams(self):
        return {
            **super().getParams(),
            "peck_depth": self.peck_depth,
            "retract_mode": self.retract_mode,
            "reentry_gap_diameters": self.reentry_gap_diameters,
            "chip_break_retract_diameters": self.chip_break_retract_diameters,
            "tip_compensation": self.tip_compensation,
        }

    def _get_gcode(self):
        """Use the shared lifecycle without insert-side dispatch."""
        self.generatePath()
        return self.generateGCode()

    def generatePath(self):
        self._reset_paths()
        if not isinstance(self.tool, Drill):
            raise ValueError("Centreline drilling requires a Drill tool")
        if self.tool.tool_rotation != 0:
            raise ValueError("Centreline drilling requires an unrotated axial drill")
        if self.containment is None:
            raise ValueError("Drilling requires explicit containment and start/final depths")
        bounds = self.containment
        values = (bounds.XMin, bounds.XMax, bounds.ZMin, bounds.ZMax, self.clearance)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Drilling limits and clearance must be finite")
        if not bounds.XMin <= 0 <= bounds.XMax or bounds.ZMin >= bounds.ZMax:
            raise ValueError("Drilling containment must include X=0 and final depth must be below start depth")
        if self.clearance <= 0:
            raise ValueError("Drilling front clearance must be positive")
        final_depth = bounds.ZMin - (self.tool.point_length if self.tip_compensation else 0)
        if not math.isfinite(final_depth):
            raise ValueError("Compensated drilling depth must be finite")
        final = Point(0, final_depth)
        if not math.isfinite(final.Z):
            raise ValueError("Compensated drilling depth must be finite at coordinate precision")
        if self.tip_compensation and final.Z >= bounds.ZMin:
            raise ValueError("Cannot represent drill-tip compensation at coordinate precision")
        if max(bounds.ZMax - final_depth, bounds.ZMax - final.Z) > self.tool.length:
            raise ValueError("Drilling depth exceeds the tool length")
        if not math.isfinite(self.peck_depth) or self.peck_depth < 0:
            raise ValueError("Peck depth must be finite and non-negative")
        if not isinstance(self.retract_mode, RetractMode):
            raise ValueError("Retract mode must be a RetractMode enumeration member")
        gap = 0
        if self.peck_depth:
            multiplier = (self.reentry_gap_diameters if self.retract_mode == RetractMode.FULL_RETRACT
                          else self.chip_break_retract_diameters)
            gap = multiplier * self.tool.diameter
            if not math.isfinite(gap) or gap <= 0:
                raise ValueError("Peck re-entry gap / chip-break retract must be finite and positive")
            if (bounds.ZMax - final.Z) / self.peck_depth > MAX_PECKS:
                raise ValueError("Peck depth would need more than {} pecks".format(MAX_PECKS))

        previous = Point(0, bounds.ZMax)
        start = previous
        groups = []
        while previous.Z > final.Z:
            if len(groups) >= MAX_PECKS:
                raise ValueError("Peck depth would need more than {} pecks".format(MAX_PECKS))
            target = (max(final.Z, bounds.ZMax - (len(groups) + 1) * self.peck_depth)
                      if self.peck_depth else final.Z)
            end = Point(0, target)
            if end.Z >= previous.Z:
                raise ValueError("Cannot advance drilling peck at coordinate precision")
            group = SegmentGroup()
            group.addSegment(Segment(start, end))
            groups.append(group)
            if end.Z > final.Z:
                start = Point(0, min(bounds.ZMax, end.Z + gap))
                if start.Z <= end.Z:
                    raise ValueError("Cannot represent peck retract at coordinate precision")
            previous = end
        self.tool_paths = groups

    def generateGCode(self):
        bounds = self.containment
        front = bounds.ZMax + self.clearance
        if not math.isfinite(front) or front <= bounds.ZMax:
            self.tool_paths = []
            raise ValueError("Cannot represent drilling front clearance at coordinate precision")
        commands = [Command("G0", {"X": 0, "Z": front})]
        for index, group in enumerate(self.tool_paths):
            cut = group.getSegments()[0]
            commands.extend([
                Command("G0", {"X": 0, "Z": cut.start.Z}),
                Command("G1", {"X": 0, "Z": cut.end.Z, "F": self.vfeed}),
            ])
            if self.retract_mode == RetractMode.FULL_RETRACT or index == len(self.tool_paths) - 1:
                commands.append(Command("G0", {"X": 0, "Z": front}))
        return commands
