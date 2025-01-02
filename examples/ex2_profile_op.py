"""
LibLathe Example 2
This example creates a profile turning operation
and writes the resulting gcode to a file.
"""
# Add LibLathe to the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.op.profile import ProfileOP
from liblathe.base.segment import Segment
from liblathe.debug.plot import Plot
from liblathe.debug.debug import Debug
from liblathe.tool.tool import Tool

# Define Part Geometry
part_segments = []
PartPt1 = Point(0, 10)
PartPt2 = Point(5, -9)
PartPt3 = Point(9.5, -15.85)
PartPt4 = Point(5.4, -22)
PartPt5 = Point(5.4, -40)
PartPt6 = Point(13, -45)
PartPt7 = Point(13, -48)
PartPt8 = Point(0, -48)

part_segments.append(Segment(PartPt1, PartPt2, 0.75))
part_segments.append(Segment(PartPt2, PartPt3))
part_segments.append(Segment(PartPt3, PartPt4))
part_segments.append(Segment(PartPt4, PartPt5))
part_segments.append(Segment(PartPt5, PartPt6))
part_segments.append(Segment(PartPt6, PartPt7))
part_segments.append(Segment(PartPt7, PartPt8))

# Define stock bounds
stockPt1 = Point(0, 15)
stockPt2 = Point(25, -55)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
params = {}
params['allow_grooving'] = True
params['step_over'] = 0.25
params['finish_passes'] = 10
params['stock_to_leave'] = 0
params['hfeed'] = 10
params['vfeed'] = 10

# Create Profile Operation
profileOP = ProfileOP()
profileOP.setParams(params)
profileOP.add_stock(StockBoundingBox)
profileOP.addPartSegments(part_segments)
tool = Tool()
tool.set_tool_from_string('DCMT070204R')
tool.set_rotation(45)
profileOP.add_tool(tool)
gcode = profileOP.getGCode()
plot = Plot()
plot.backplot(gcode)

segment_groups = [profileOP.partSegmentGroup, tool.get_segmentgroup()]

# Append all tool paths to be drawn
for segmentgroup in profileOP.tool_paths:
    segment_groups.append(segmentgroup)

Debug().draw(segment_groups)

# Write the gcode to a file in the Examples folder
f = open(thisFolder + "/profile.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
