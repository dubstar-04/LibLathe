"""
Offset Test to support development and debugging
This example creates profile offsets and writes the segments to an image file
"""
# Add LibLathe is in the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup
from liblathe.plot import Plot

# Define Part Geometry
segment_group = SegmentGroup()

PartPt1 = Point(0, 0, 10)
PartPt2 = Point(-5, 0, -9)
PartPt3 = Point(-9.5, 0, -15.85)
PartPt4 = Point(-5.4, 0, -22)
PartPt5 = Point(-5.4, 0, -40)
PartPt6 = Point(-13, 0, -45)
PartPt7 = Point(-13, 0, -48)
PartPt8 = Point(0, 0, -48)

segment_group.add_segment(Segment(PartPt1, PartPt2, -0.75))
segment_group.add_segment(Segment(PartPt2, PartPt3))
segment_group.add_segment(Segment(PartPt3, PartPt4))
segment_group.add_segment(Segment(PartPt4, PartPt5))
segment_group.add_segment(Segment(PartPt5, PartPt6))
segment_group.add_segment(Segment(PartPt6, PartPt7))
segment_group.add_segment(Segment(PartPt7, PartPt8))

groups = []

groups.append(segment_group)
# add additional offsets
for step_over in range(30):
    groups.append(segment_group.offset_path(step_over))


plot = Plot()
plot.debug_segment_group(groups)
