"""
LibLathe Example 1
This example creates a profile turning operation
and writes the resulting gcode to a file.
"""
# Add LibLathe is in the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.boundbox import BoundBox
from liblathe.point import Point
from liblathe.profile_op import ProfileOP
from liblathe.segment import Segment
# from liblathe.plot import Plot
from liblathe.tool import Tool

# Define Part Geometry
part_segments = []

PartPt1 = Point(0, 0, 0)
PartPt2 = Point(-15, 0, -5)
PartPt3 = Point(-15, 0, -15)
PartPt4 = Point(0, 0, -20)

part_segments.append(Segment(PartPt1, PartPt2))
part_segments.append(Segment(PartPt2, PartPt3))
part_segments.append(Segment(PartPt3, PartPt4))
part_segments.append(Segment(PartPt4, PartPt1))

# Define stock bounds
stockPt1 = Point(0, 0, 5)
stockPt2 = Point(-20, 0, -20)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
params = {}
params['min_dia'] = 0
params['extra_dia'] = 0
params['start_offset'] = 0
params['end_offset'] = 0
params['allow_grooving'] = False
params['step_over'] = 1
params['finish_passes'] = 2
params['stock_to_leave'] = 0
params['hfeed'] = 10
params['vfeed'] = 10

# Create Profile Operation
profileOP = ProfileOP()
profileOP.set_params(params)
profileOP.add_stock(StockBoundingBox)
profileOP.add_part_edges(part_segments)
tool = Tool()
tool.set_tool_from_string('DCMT070204R')
profileOP.add_tool(tool)
gcode = profileOP.get_gcode()
# plot = Plot()
# plot.backplot(gcode)

# Write the gcode to a file in the Examples folder
f = open(thisFolder + "/profile.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
