"""Machine an internal contour with separate Internal Rough and Profile operations."""

import argparse
import os
import sys
from pathlib import Path

thisFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(thisFolder))

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.debug.debug import Debug
from liblathe.debug.plot import Plot
from liblathe.op.base import Direction, MachiningMode
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP
from liblathe.tool.tool import Tool

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path(thisFolder))
parser.add_argument("--no-show", action="store_true")
args = parser.parse_args()
if not args.output.is_dir():
    parser.error("--output must be an existing directory")

vertices = [(12, 0), (12, -10), (10, -15), (10, -30), (0, -30)]
part = [Segment(Point(*start), Point(*end))
        for start, end in zip(vertices, vertices[1:])]
containment = BoundBox(Point(0, -30), Point(15, 0))
stock = BoundBox(Point(0, -35), Point(20, 2))
tool_vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
tool = Tool()
tool.set_tool_from_segments([
    Segment(Point(*start), Point(*end))
    for start, end in zip(tool_vertices, tool_vertices[1:])
])

rough = RoughOP()
rough.setParams({
    "mode": MachiningMode.INTERNAL,
    "direction": Direction.RADIAL,
    "allow_grooving": True,
    "pass_offset": 0.5,
    "stock_to_leave": 0.2,
    "clearance": 2,
})
rough.add_containment(containment)
rough.add_stock(stock)
rough.addPartSegments(part)
rough.add_tool(tool)
rough_code = rough.getGCode()

profile = ProfileOP()
profile.setParams({
    "mode": MachiningMode.INTERNAL,
    "direction": Direction.RADIAL,
    "pass_offset": 0.5,
    "finish_passes": 3,
    "clearance": 2,
})
profile.add_containment(containment)
profile.add_stock(stock)
profile.addPartSegments(part)
profile.add_tool(tool)
profile_code = profile.getGCode()

plot = Plot()
plot.set_file_path(str(args.output.resolve()) + os.sep)
plot.image_name = "internal_rough_profile"
plot.image_type = ".png"
plot.backplot(list(rough_code) + list(profile_code))
for name, commands in (("internal_rough.gcode", rough_code),
                       ("internal_profile.gcode", profile_code)):
    with (args.output / name).open("w", encoding="utf-8") as output:
        output.writelines(command.to_string() + "\n" for command in commands)

print("No pre-existing opening, bar, holder or tool-fit checks are performed.")
print("Rough paths:", len(rough.tool_paths),
      "Profile paths:", len(profile.tool_paths))
print("Plot:", args.output / "internal_rough_profile.png")
if not args.no_show:
    Debug().draw([rough.partSegmentGroup, *rough.tool_paths, *profile.tool_paths])
