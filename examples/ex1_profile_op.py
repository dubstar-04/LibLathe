"""
LibLathe Example 1
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
part_segments.append(Segment(Point(0, 0), Point(14, -15), 0.3))
part_segments.append(Segment(Point(14, -15), Point(14, -75) , 0.000000))
part_segments.append(Segment(Point(14, -75), Point(27.5, -85) , 0.000000))
part_segments.append(Segment(Point(27.5, -85), Point(27.5, -100.0) , 0.000000))
part_segments.append(Segment(Point(27.5, -100.0), Point(0.0, -100.0) , 0.000000))

"""
# segments reversed from above
part_segments.append(Segment(Point(0.0, -100.0) ,Point(27.5, -100.0), 0.000000))
part_segments.append(Segment(Point(27.5, -100.0) ,Point(27.5, -85), 0.000000))
part_segments.append(Segment(Point(27.5, -85) ,Point(14, -75), 0.000000))
part_segments.append(Segment(Point(14, -75) ,Point(14, -15), 0.000000))
part_segments.append(Segment(Point(14, -15) ,Point(0, 0), -0.3))
"""


# Define stock bounds
stockPt1 = Point(0, -150)
stockPt2 = Point(50, 10)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
params = {}
params['min_dia'] = 0
params['extra_dia'] = 0
params['start_offset'] = 0
params['end_offset'] = 0
params['allow_grooving'] = False
params['step_over'] = 0.5
params['finish_passes'] = 5
params['stock_to_leave'] = 0.5
params['hfeed'] = 10
params['vfeed'] = 10

# Create Profile Operation
profileOP = ProfileOP()
profileOP.set_params(params)
profileOP.add_stock(StockBoundingBox)
profileOP.add_part_edges(part_segments)
tool = Tool()
tool.set_tool_from_string('DCMT070204R')
tool.set_rotation(22.5)
profileOP.add_tool(tool)
gcode = profileOP.get_gcode()
plot = Plot()
plot.backplot(gcode)

segment_groups = [profileOP.part_segment_group, tool.get_shape_group()]

# Append all tool paths to be drawn
for segmentgroup in profileOP.tool_paths:
    segment_groups.append(segmentgroup)

Debug().draw(segment_groups)

# Write the gcode to a file in the Examples folder
f = open(thisFolder + "/profile.gcode", "w")

for command in gcode:
    f.write(command.to_string() + "\n")

f.close()
