"""Internal clearing and finishing; prepared opening and tool assembly fit are NOT checked.

Run: python examples/ex7_bore_op.py --no-show --output /existing/directory
"""

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
from liblathe.op.bore import BoreOP
from liblathe.op.base import CutDirection
from liblathe.tool.tool import Tool

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path(thisFolder))
parser.add_argument("--no-show", action="store_true")
parser.add_argument("--direction", choices=("X", "Z"), default="X")
args = parser.parse_args()
if not args.output.is_dir():
    parser.error("--output must be an existing directory")

# The target inner wall runs from the mouth into the part, then across a blind floor.
vertices = [(12, 0), (12, -10), (10, -15), (10, -30), (0, -30)]
operation = BoreOP()
operation.addPartSegments([
    Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
operation.add_containment(BoundBox(Point(0, -30), Point(15, 0)))
operation.setParams({
    "finish_passes": 3, "pass_offset": 0.5, "cut_direction": CutDirection(args.direction),
    "stock_to_leave": 0.2, "clearance": 2, "hfeed": 100})

# Outward-facing insert tip at (0, 0); this is not a boring-bar/holder model.
vertices = [(-2, 0), (0, 0), (0, 2), (-2, 2), (-2, 0)]
tool = Tool()
tool.set_tool_from_segments([
    Segment(Point(*start), Point(*end)) for start, end in zip(vertices, vertices[1:])])
operation.add_tool(tool)
commands = operation.getGCode()

plot = Plot()
plot.set_file_path(str(args.output.resolve()) + "/")
plot.image_name = "bore_toolpath"
plot.image_type = ".png"
plot.backplot(list(commands))
with (args.output / "bore.gcode").open("w") as output:
    for command in commands:
        output.write(command.to_string() + "\n")

print("EXPERIMENTAL: no prepared-opening, access, bar or holder clearance checks.")
print("Clearing strokes:", len(operation.clearing_paths),
      "Finishing strokes:", len(operation.tool_paths), "Commands:", len(commands))
print("Plot:", args.output / "bore_toolpath.png")
if not args.no_show:
    Debug().draw([operation.partSegmentGroup, *operation.clearing_paths, *operation.tool_paths])
