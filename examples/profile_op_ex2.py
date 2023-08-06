"""
LibLathe Example 2
This example creates a profile turning operation
and writes the resulting gcode to a file.
"""
# Add LibLathe is in the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.profile_op import ProfileOP
from liblathe.base.segment import Segment
from liblathe.plot import Plot
from liblathe.base.tool import Tool

# Define Part Geometry
part_segments = []

PartPt1 = Point(0, 0, 10)
PartPt2 = Point(-5, 0, -9)
PartPt3 = Point(-9.5, 0, -15.85)
PartPt4 = Point(-5.4, 0, -22)
PartPt5 = Point(-5.4, 0, -40)
PartPt6 = Point(-13, 0, -45)
PartPt7 = Point(-13, 0, -48)
PartPt8 = Point(0, 0, -48)

part_segments.append(Segment(PartPt1, PartPt2, -0.75))
part_segments.append(Segment(PartPt2, PartPt3))
part_segments.append(Segment(PartPt3, PartPt4))
part_segments.append(Segment(PartPt4, PartPt5))
part_segments.append(Segment(PartPt5, PartPt6))
part_segments.append(Segment(PartPt6, PartPt7))
part_segments.append(Segment(PartPt7, PartPt8))

# Define stock bounds
stockPt1 = Point(0, 0, 15)
stockPt2 = Point(-25, 0, -55)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
params = {}
params['min_dia'] = 0
params['extra_dia'] = 0
params['start_offset'] = 0
params['end_offset'] = 0
params['allow_grooving'] = True
params['step_over'] = 0.25
params['finish_passes'] = 10
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
tool.set_rotation(75)
profileOP.add_tool(tool)
gcode = profileOP.get_gcode()
plot = Plot()
plot.backplot(gcode)

# Write the gcode to a file in the Examples folder
f = open(thisFolder + "/profile.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
