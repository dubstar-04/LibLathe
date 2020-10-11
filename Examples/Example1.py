# LibLathe Example 1

# Add LibLathe is in the Python Path
import os, sys
parentFolder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parentFolder)

from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment
from LibLathe.LLProfileOP import ProfileOP
from LibLathe.LLBoundBox import BoundBox


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
stockPt1 = Point(0, 0, 0)
stockPt2 = Point(-20, 0, -20)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# Define Operations Properties
props = {}
props['min_dia']=0
props['extra_dia']=0
props['start_offset']=0
props['end_offset']=0
props['allow_grooving']=False
props['allow_facing']=False
props['step_over']=1
props['finish_passes']=2
props['hfeed' ]=10
props['vfeed']=10

# Create Profile Operation
profileOP = ProfileOP()
profileOP.set_params(props)
profileOP.add_stock(StockBoundingBox)
profileOP.add_part_edges(part_segments)
gcode = profileOP.get_gcode()

for line in gcode:
    for command in line:
        print(command.get_movement(), command.get_params())
