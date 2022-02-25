"""
Offset Test to support development and debugging
This example creates profile offsets and writes the segments to an image file
"""
# Add LibLathe is in the Python Path
import os
import sys
import math

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.segmentgroup import SegmentGroup
from liblathe.plot import Plot

# Define Part Geometry
segment_group = SegmentGroup()

'''
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
'''


Pt1 = Point(0.0000, 0, 60.0000)
Pt2 = Point(-7.0711, 0, 42.9289)
Pt3 = Point(-14.1421, 0, 35.8579)
Pt4 = Point(-10.6066, 0, 32.3223)
Pt5 = Point(-5.6066, 0, 32.3223)
Pt6 = Point(-5.6066, 0, 27.3223)
Pt7 = Point(-8.1066, 0, 27.3223)
Pt8 = Point(-8.1066, 0, 17.3223)
Pt9 = Point(-8.1066, 0, 12.3223)
Pt10 = Point(-8.1066, 0, 2.3223)
Pt11 = Point(-8.1066, 0, -7.6777)
Pt12 = Point(-8.1066, 0, -17.6777)
Pt13 = Point(-11.6421, 0, -26.2132)
Pt14 = Point(-20.4570, 0, -35.0280)
Pt15 = Point(-20.4570, 0, -40.0280)
Pt16 = Point(0.0000, 0, -40.0280)

segment_group.add_segment(Segment(Pt1, Pt2, math.tan(math.radians(-135) / 4)))  # rad 20
segment_group.add_segment(Segment(Pt2, Pt3))
segment_group.add_segment(Segment(Pt3, Pt4))
segment_group.add_segment(Segment(Pt4, Pt5))
segment_group.add_segment(Segment(Pt5, Pt6))
segment_group.add_segment(Segment(Pt6, Pt7))
segment_group.add_segment(Segment(Pt7, Pt8))
segment_group.add_segment(Segment(Pt8, Pt9, math.tan(math.radians(-180) / 4)))  # rad 2.5
segment_group.add_segment(Segment(Pt9, Pt10))
segment_group.add_segment(Segment(Pt10, Pt11, math.tan(math.radians(180) / 4)))  # rad 5
segment_group.add_segment(Segment(Pt11, Pt12))
segment_group.add_segment(Segment(Pt12, Pt13, math.tan(math.radians(225) / 4)))   # rad 5
segment_group.add_segment(Segment(Pt13, Pt14))
segment_group.add_segment(Segment(Pt14, Pt15))
segment_group.add_segment(Segment(Pt15, Pt16))

groups = []

groups.append(segment_group)
# add additional offsets
for step_over in range(10):
    groups.append(segment_group.offset_path(step_over))


plot = Plot()
plot.backplot(groups)
