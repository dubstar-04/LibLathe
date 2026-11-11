"""
LibLathe Example 3
This example creates a roughing turning operation
and plots advisory remaining stock using LibLathe's native StockPreview.

Run:
    python examples/ex3_rough_op.py --no-show
"""
# Add LibLathe to the Python Path
import argparse
import math
import os
import sys
from pathlib import Path

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.op.rough import RoughOP
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup, StockPreview
from liblathe.debug.plot import Plot
from liblathe.debug.debug import Debug
from liblathe.tool.tool import Tool


def group(edges):
    result = SegmentGroup()
    for x0, z0, x1, z1 in edges:
        result.addSegment(Segment(Point(x0, z0), Point(x1, z1)))
    return result


def sample_tool(segments, tolerance=0.005):
    """Approximate curved insert edges with inscribed chords for the guide."""
    points = []
    for edge in segments:
        if not edge.bulge:
            points.append((edge.start.X, edge.start.Z))
            continue
        centre = edge.getCentrePoint()
        radius = edge.getRadius()
        sweep = -4 * math.atan(edge.bulge)
        angle = math.atan2(edge.start.Z - centre.Z, edge.start.X - centre.X)
        step = 2 * math.acos(max(-1, 1 - tolerance / radius))
        count = max(1, math.ceil(abs(sweep) / step))
        for i in range(count):
            a = angle + sweep * i / count
            points.append((centre.X + radius * math.cos(a), centre.Z + radius * math.sin(a)))
    return points


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path(thisFolder))
parser.add_argument("--no-show", action="store_true", help="Save plots without opening a viewer")
args = parser.parse_args()
if not args.output.is_dir():
    parser.error("--output must be an existing directory")

# Define Part Geometry
partSegments = []
partSegments.append(Segment(Point(0.0, -100.0), Point(27.5, -100.0), 0.000000))
partSegments.append(Segment(Point(27.5, -100.0), Point(27.5, -85), 0.000000))
partSegments.append(Segment(Point(27.5, -85), Point(14, -75), 0.000000))
partSegments.append(Segment(Point(14, -75), Point(14, -15), 0.000000))
partSegments.append(Segment(Point(14, -15), Point(0, 0), -0.3))

# Define containment bounds
# Leave the back face outside this external roughing operation.
containmentPt1 = Point(0, -95)
containmentPt2 = Point(35, 15)
ContainmentBoundingBox = BoundBox(containmentPt1, containmentPt2)

# Define Operations Properties
params = {}
params['allow_grooving'] = True
params['pass_offset'] = 0.5
params['finish_passes'] = 0
params['stock_to_leave'] = 1
params['hfeed'] = 10
params['vfeed'] = 10

# Create Profile Operation
roughOP = RoughOP()
roughOP.setParams(params)
roughOP.add_containment(ContainmentBoundingBox)
roughOP.add_stock(BoundBox(Point(0, -105), Point(35, 15)))
roughOP.addPartSegments([
    Segment(segment.end, segment.start, -segment.bulge)
    for segment in reversed(partSegments)])
tool = Tool()
tool.set_tool_from_string('DCMT070204R')
# tool.set_rotation(45)
roughOP.add_tool(tool)
gcode = roughOP.getGCode()

insert = sample_tool(tool.get_segmentgroup().getSegments())
moves = []
previous = None
for command in gcode:
    params = command.getParams()
    if "X" not in params or "Z" not in params:
        continue
    current = (params["X"], params["Z"])
    if previous is not None:
        if command.get_movement() in ("G2", "G3"):
            raise ValueError("The stock guide supports straight feeds only")
        if command.get_movement() == "G1":
            moves.append((*previous, *current))
    previous = current

bounds = roughOP.stock
stock = [(bounds.XMin, bounds.ZMin), (bounds.XMax, bounds.ZMin),
         (bounds.XMax, bounds.ZMax), (bounds.XMin, bounds.ZMax)]
original_stock = StockPreview(stock)
remaining = original_stock.copy()
remaining.remove_feeds(insert, moves)
edges = remaining.edges()
boundary_area = math.fsum((x0 * z1 - x1 * z0) / 2
                          for x0, z0, x1, z1 in edges)
if not math.isclose(boundary_area, remaining.area, rel_tol=1e-7, abs_tol=1e-8):
    raise RuntimeError("Exported stock boundary fails the signed-area check")
stock_plot = Plot()
stock_plot.set_file_path(str(args.output.resolve()) + "/")
stock_plot.image_name = "rough_remaining_stock"
stock_plot.image_type = ".png"
stock_plot.set_background_colour((245, 245, 245))
stock_plot.set_path_colour("G1", (150, 90, 15))
stock_plot.backplot([group(edges), group([
    (*a, *b) for a, b in zip(stock, stock[1:] + stock[:1])])])
print("Remaining stock plot:", args.output / "rough_remaining_stock.png")
print("Remaining area:", remaining.area, "square model units;",
      "uncertain retained cuts:", remaining.uncertain_retentions)

plot = Plot()
plot.set_file_path(str(args.output.resolve()) + "/")
plot.image_name = "rough_toolpath"
plot.backplot(list(gcode))

segmentGroups = [roughOP.partSegmentGroup]

# Append all tool paths to be drawn
for segmentgroup in roughOP.tool_paths:
    segmentGroups.append(segmentgroup)

if not args.no_show:
    Debug().draw(segmentGroups)

# Write the gcode to a file in the Examples folder
f = open(args.output / "profile.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
