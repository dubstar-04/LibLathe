"""Centreline drill with its tip at the origin and shank toward positive Z."""

import math

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.tool.tool import Tool


class Drill(Tool):
    def __init__(self, diameter, tip_angle=118, length=50):
        super().__init__()
        if not all(math.isfinite(value) for value in (diameter, tip_angle, length)):
            raise ValueError("Drill dimensions must be finite")
        if diameter <= 0 or length <= 0 or not 0 < tip_angle < 180:
            raise ValueError("Drill diameter and length must be positive; tip angle must be between 0 and 180 degrees")
        self.diameter = diameter
        self.tip_angle = tip_angle
        self.length = length
        self.point_length = diameter / (2 * math.tan(math.radians(tip_angle / 2)))
        if self.point_length >= length:
            raise ValueError("Drill length must exceed its point length")
        radius = diameter / 2
        vertices = [Point(0, 0), Point(radius, self.point_length), Point(radius, length),
                    Point(-radius, length), Point(-radius, self.point_length)]
        self.set_tool_from_segments([
            Segment(start, end) for start, end in zip(vertices, vertices[1:] + vertices[:1])])
