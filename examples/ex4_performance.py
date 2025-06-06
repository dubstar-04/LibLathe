"""
LibLathe Example 4
This example creates a profing operation
outputing time stamps to measure performance
"""

# Add LibLathe to the Python Path
import os
import sys
import time

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.boundbox import BoundBox

from liblathe.debug.debug import Debug

start_time = time.time()

# add shape points
Pt1 = Point(0, 10)
Pt2 = Point(2.36, 9.72)
Pt3 = Point(4.58, 8.89)
Pt4 = Point(6.55, 7.56)
Pt5 = Point(8.15, 5.80)
Pt6 = Point(9.28, 3.72)
Pt7 = Point(9.9, 1.42)
Pt8 = Point(9.95, -0.95)
Pt9 = Point(9.45, -3.27)
Pt10 = Point(8.41, -5.41)
Pt11 = Point(6.90, -7.24)
Pt12 = Point(5, -9)
Pt13 = Point(9.5, -15.85)
Pt14 = Point(5.4, -22)
Pt15 = Point(4.03, -22.68)
Pt16 = Point(3.01, -23.81)
Pt17 = Point(2.45, -25.23)
Pt18 = Point(2.45, -26.76)
Pt19 = Point(3.00, -28.18)
Pt20 = Point(4.02, -29.31)
Pt21 = Point(5.4, -30)
Pt22 = Point(5.4, -40)
Pt23 = Point(13, -45)
Pt24 = Point(13, -48)
Pt25 = Point(0, -48)

sg = SegmentGroup()
sg.addSegment(Segment(Pt1, Pt2))
sg.addSegment(Segment(Pt2, Pt3))
sg.addSegment(Segment(Pt3, Pt4))
sg.addSegment(Segment(Pt4, Pt5))
sg.addSegment(Segment(Pt5, Pt6))
sg.addSegment(Segment(Pt6, Pt7))
sg.addSegment(Segment(Pt7, Pt8))
sg.addSegment(Segment(Pt8, Pt9))
sg.addSegment(Segment(Pt9, Pt10))
sg.addSegment(Segment(Pt10, Pt11))
sg.addSegment(Segment(Pt11, Pt12))
sg.addSegment(Segment(Pt12, Pt13))
sg.addSegment(Segment(Pt13, Pt14))
sg.addSegment(Segment(Pt14, Pt15))
sg.addSegment(Segment(Pt15, Pt16))
sg.addSegment(Segment(Pt16, Pt17))
sg.addSegment(Segment(Pt17, Pt18))
sg.addSegment(Segment(Pt18, Pt19))
sg.addSegment(Segment(Pt19, Pt20))
sg.addSegment(Segment(Pt20, Pt21))
sg.addSegment(Segment(Pt21, Pt22))
sg.addSegment(Segment(Pt22, Pt23))
sg.addSegment(Segment(Pt23, Pt24))
sg.addSegment(Segment(Pt24, Pt25))

# define tool shape
tool_point_1 = Point(0, 0)
tool_point_2 = Point(0, 5)
tool_point_3 = Point(5, 5)
tool_point_4 = Point(5, 0)

tool = SegmentGroup()
tool.addSegment(Segment(tool_point_1, tool_point_2))
tool.addSegment(Segment(tool_point_2, tool_point_3))
tool.addSegment(Segment(tool_point_3, tool_point_4))
tool.addSegment(Segment(tool_point_4, tool_point_1))

print('count', sg.count())

part_boundbox = sg.boundbox()
print("bb:", part_boundbox.XMin, part_boundbox.ZMin, part_boundbox.XMax, part_boundbox.ZMax)
stock_min = Point(part_boundbox.XMin, part_boundbox.ZMin - 5)
stock_max = Point(part_boundbox.XMax + 5, part_boundbox.ZMax + 5)
stock = BoundBox(stock_min, stock_max)

init_time = time.time()
print("Init time: ", init_time - start_time)

defeatured_group = sg.defeature(stock, tool, True)

defeature_time = time.time()
print("Defeature time: ", defeature_time - init_time)

print('defeatured group size', defeatured_group.count())

segmentGroups = []
segmentGroups.append(sg)
segmentGroups.append(defeatured_group)
segmentGroups.append(tool)

offset_time = time.time()

# Base offset time:
# 0.35 seconds - original quadtree implementation
# 0.09 seconds - using a square base node
# 0.015 seconds - using node size as limit, returning the found points from quadtree build

for i in range(1, 5, 1):
    segmentGroups.append(defeatured_group.offset(i))
    iteration_time = time.time()
    print("Offset time:", i, ": ",  iteration_time - offset_time)
    offset_time = iteration_time

Debug().draw(segmentGroups)
