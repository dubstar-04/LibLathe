"""Use separate Rough and Profile strategies to machine a pair of grooves."""

import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(thisFolder))

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.debug.debug import Debug
from liblathe.debug.plot import Plot
from liblathe.op.base import Direction
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP
from liblathe.tool.tool import Tool

vertices = [(0, 0), (15, 0), (15, -10), (10, -10), (10, -20),
            (15, -20), (15, -26), (12, -26), (12, -30), (15, -30),
            (15, -40), (0, -40)]
part = [Segment(Point(*start), Point(*end))
        for start, end in zip(vertices, vertices[1:])]
containment = BoundBox(Point(0, -40), Point(16, 0))

tool_width = 2
tool_vertices = [(0, 0), (0, -tool_width), (tool_width, -tool_width),
                 (tool_width, 0), (0, 0)]
tool = Tool()
tool.set_tool_shape("S")
tool.set_tool_from_segments([
    Segment(Point(*start), Point(*end))
    for start, end in zip(tool_vertices, tool_vertices[1:])
])

rough = RoughOP()
rough.setParams({
    "direction": Direction.RADIAL,
    "pass_offset": 1.5,
    "allow_grooving": True,
    "stock_to_leave": 0.2,
    "hfeed": 10,
    "vfeed": 10,
})
rough.add_containment(containment)
rough.addPartSegments(part)
rough.add_tool(tool)
rough_code = rough.getGCode()

profile = ProfileOP()
profile.setParams({
    "direction": Direction.RADIAL,
    "pass_offset": 0.5,
    "finish_passes": 2,
    "allow_grooving": True,
    "hfeed": 10,
    "vfeed": 10,
})
profile.add_containment(containment)
profile.addPartSegments(part)
profile.add_tool(tool)
profile_code = profile.getGCode()

plot = Plot()
plot.backplot(list(rough_code) + list(profile_code))
Debug().draw([rough.partSegmentGroup, *rough.tool_paths, *profile.tool_paths])

for filename, commands in (("rough.gcode", rough_code), ("profile.gcode", profile_code)):
    with open(os.path.join(thisFolder, filename), "w", encoding="utf-8") as output:
        output.writelines(command.to_string() + "\n" for command in commands)
