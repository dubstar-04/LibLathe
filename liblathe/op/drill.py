"""Experimental straight centreline drilling, programmed at the drill tip."""

import math

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.gcode.command import Command
from liblathe.op.base import BaseOP
from liblathe.tool.drill import Drill


class DrillOP(BaseOP):
    def getGCode(self):
        self.generatePath()
        return self.generateGCode()

    def generatePath(self):
        self.tool_paths = []
        self.clearing_paths = []
        if not isinstance(self.tool, Drill):
            raise ValueError("Centreline drilling requires a Drill tool")
        if self.tool.tool_rotation != 0:
            raise ValueError("Centreline drilling requires an unrotated axial drill")
        if self.containment is None:
            raise ValueError("Drilling requires explicit containment and tip depths")
        bounds = self.containment
        values = (bounds.XMin, bounds.XMax, bounds.ZMin, bounds.ZMax, self.clearance)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Drilling limits and clearance must be finite")
        if not bounds.XMin <= 0 <= bounds.XMax or bounds.ZMin >= bounds.ZMax:
            raise ValueError("Drilling containment must include X=0 and final depth must be below start depth")
        if self.clearance <= 0:
            raise ValueError("Drilling front clearance must be positive")
        if bounds.ZMax - bounds.ZMin > self.tool.length:
            raise ValueError("Drilling depth exceeds the tool length")
        group = SegmentGroup()
        group.addSegment(Segment(Point(0, bounds.ZMax), Point(0, bounds.ZMin)))
        self.tool_paths = [group]

    def generateGCode(self):
        bounds = self.containment
        front = bounds.ZMax + self.clearance
        if not math.isfinite(front):
            self.tool_paths = []
            raise ValueError("Drilling front clearance must be finite")
        return [
            Command("G0", {"X": 0, "Z": front}),
            Command("G0", {"X": 0, "Z": bounds.ZMax}),
            Command("G1", {"X": 0, "Z": bounds.ZMin, "F": self.vfeed}),
            Command("G0", {"X": 0, "Z": front}),
        ]
