# Add LibLathe is in the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.boundbox import BoundBox
from liblathe.tool.tool import Tool

from liblathe.debug.debug import Debug

def defeature_test():
    sg = SegmentGroup()
    sg.add_segment(Segment(Point(0.000000, 0.000000), Point(14.000000, 0.000000), 0.000000))
    sg.add_segment(Segment(Point(14.000000, 0.000000), Point(14.000000, 3.000000), 0.000000))
    sg.add_segment(Segment(Point(14.000000, 3.000000), Point(10.024446, 3.000000), 0.000000))
    sg.add_segment(Segment(Point(10.024446, 3.000000), Point(10.024446, 16.503675), 0.000000))
    sg.add_segment(Segment(Point(10.024446, 16.503675), Point(7.823956, 20.415653), 0.000000))
    sg.add_segment(Segment(Point(7.823956, 20.415653), Point(7.823956, 24.816635), 0.000000))
    sg.add_segment(Segment(Point(7.823956, 24.816635), Point(5.378980, 28.484116), 0.000000))
    sg.add_segment(Segment(Point(5.378980, 28.484116), Point(5.378980, 33.618591), 0.000000))
    sg.add_segment(Segment(Point(5.378980, 33.618591), Point(7.579464, 37.775074), 0.000000))
    sg.add_segment(Segment(Point(7.579464, 37.775074), Point(5.378980, 40.220055), 0.000000))
    sg.add_segment(Segment(Point(5.378980, 40.220055), Point(5.351727, 42.823235), -0.021046))
    sg.add_segment(Segment(Point(5.351727, 42.823235), Point(0.000000, 47.587715), -0.386726))

    part_boundbox = sg.boundbox()
    stock_min = Point(part_boundbox.x_min, part_boundbox.z_min - 5)
    stock_max = Point(part_boundbox.x_max + 5, part_boundbox.z_max + 5)
    stock = BoundBox(stock_min, stock_max)

    # define tool shape
    tool = Tool()
    tool.set_tip_angle(55)
    tool.set_edge_length(6)

    defeatured_group = sg.defeature(stock, tool.get_shape_group(), True)

    Debug().draw([sg, defeatured_group]) #, tool.get_shape_group()])


defeature_test()
