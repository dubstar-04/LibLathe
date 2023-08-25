# Add LibLathe is in the Python Path
import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.boundbox import BoundBox

from liblathe.debug.debug import Debug

start_time = time.time()

def quadtree_test():

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
    sg.add_segment(Segment(Pt1, Pt2))
    sg.add_segment(Segment(Pt2, Pt3))
    sg.add_segment(Segment(Pt3, Pt4))
    sg.add_segment(Segment(Pt4, Pt5))
    sg.add_segment(Segment(Pt5, Pt6))
    sg.add_segment(Segment(Pt6, Pt7))
    sg.add_segment(Segment(Pt7, Pt8))
    sg.add_segment(Segment(Pt8, Pt9))
    sg.add_segment(Segment(Pt9, Pt10))
    sg.add_segment(Segment(Pt10, Pt11))
    sg.add_segment(Segment(Pt11, Pt12))
    sg.add_segment(Segment(Pt12, Pt13))
    sg.add_segment(Segment(Pt13, Pt14))
    sg.add_segment(Segment(Pt14, Pt15))
    sg.add_segment(Segment(Pt15, Pt16))
    sg.add_segment(Segment(Pt16, Pt17))
    sg.add_segment(Segment(Pt17, Pt18))
    sg.add_segment(Segment(Pt18, Pt19))
    sg.add_segment(Segment(Pt19, Pt20))
    sg.add_segment(Segment(Pt20, Pt21))
    sg.add_segment(Segment(Pt21, Pt22))
    sg.add_segment(Segment(Pt22, Pt23))
    sg.add_segment(Segment(Pt23, Pt24))
    sg.add_segment(Segment(Pt24, Pt25))

    # define tool shape
    tool_point_1 = Point(0, 0)
    tool_point_2 = Point(0, 5)
    tool_point_3 = Point(5, 5)
    tool_point_4 = Point(5, 0)

    tool = SegmentGroup()
    tool.add_segment(Segment(tool_point_1, tool_point_2))
    tool.add_segment(Segment(tool_point_2, tool_point_3))
    tool.add_segment(Segment(tool_point_3, tool_point_4))
    tool.add_segment(Segment(tool_point_4, tool_point_1))

    print('count', sg.count())

    part_boundbox = sg.boundbox()
    print("bb:", part_boundbox.x_min, part_boundbox.z_min, part_boundbox.x_max, part_boundbox.z_max)
    stock_min = Point(part_boundbox.x_min, part_boundbox.z_min - 5)
    stock_max = Point(part_boundbox.x_max + 5, part_boundbox.z_max + 5)
    stock = BoundBox(stock_min, stock_max)

    init_time = time.time()
    print("Init time: ", init_time - start_time)

    defeatured_group = sg.defeature(stock, tool, True)

    defeature_time = time.time()
    print("Defeature time: ", defeature_time - init_time)

    print('defeatured group size', defeatured_group.count())

    offset_time = time.time()
    print("Offset time: ", offset_time - init_time)

    segment_groups = []
    segment_groups.append(sg)
    segment_groups.append(defeatured_group)

    for i in range(1, 5, 1):
        segment_groups.append(defeatured_group.offset(i))

    Debug().draw(segment_groups)

quadtree_test()
