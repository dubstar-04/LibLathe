"""
LibLathe Example 6
This example creates a grooving turning operation
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
from liblathe.op.groove import GrooveOP
from liblathe.base.segment import Segment
from liblathe.debug.plot import Plot
from liblathe.debug.debug import Debug
from liblathe.tool.tool import Tool

# Define Part Geometry with a wide groove and a narrow groove
partSegments = []
partSegments.append(Segment(Point(0.0, 0.0), Point(15, 0.0)))
partSegments.append(Segment(Point(15, 0.0), Point(15, -10)))
partSegments.append(Segment(Point(15, -10), Point(10, -10)))
partSegments.append(Segment(Point(10, -10), Point(10, -20)))
partSegments.append(Segment(Point(10, -20), Point(15, -20)))
partSegments.append(Segment(Point(15, -20), Point(15, -26)))
partSegments.append(Segment(Point(15, -26), Point(12, -26)))
partSegments.append(Segment(Point(12, -26), Point(12, -30)))
partSegments.append(Segment(Point(12, -30), Point(15, -30)))
partSegments.append(Segment(Point(15, -30), Point(15, -40)))
partSegments.append(Segment(Point(15, -40), Point(0.0, -40)))

# Define stock bounds
# The stock Z limits set the section to groove and the X limits set the max and min diameters
# e.g. BoundBox(Point(0, -20), Point(16, -10)) grooves only the wide groove
stockPt1 = Point(0, -40)
stockPt2 = Point(16, 0)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
params = {}
params['pass_offset'] = 1.5
params['finish_passes'] = 1
params['stock_to_leave'] = 0
params['hfeed'] = 10
params['vfeed'] = 10

# Define a 2mm wide square (S shape) grooving tool
# ISO S codes start at 3.97mm so the tool is built from segments
toolWidth = 2
toolPoints = [Point(0, 0), Point(0, -toolWidth), Point(toolWidth, -toolWidth), Point(toolWidth, 0), Point(0, 0)]
tool = Tool()
tool.set_tool_shape('S')
tool.set_tool_from_segments([Segment(start, end) for start, end in zip(toolPoints, toolPoints[1:])])

# Create Groove Operation
grooveOP = GrooveOP()
grooveOP.setParams(params)
grooveOP.add_stock(StockBoundingBox)
grooveOP.addPartSegments(partSegments)
grooveOP.add_tool(tool)
gcode = grooveOP.getGCode()
plot = Plot()
plot.backplot(list(gcode))

segmentGroups = [grooveOP.partSegmentGroup]

# Append all tool paths to be drawn
for segmentgroup in grooveOP.tool_paths:
    segmentGroups.append(segmentgroup)

Debug().draw(segmentGroups)

# Write the gcode to a file in the Examples folder
f = open(thisFolder + "/groove.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
