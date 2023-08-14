"""
LibLathe Offsetting Test
Test creating turning offsets using a signed distance field
"""
# Add LibLathe is in the Python Path
import os
import sys
import math
import time
from PIL import Image, ImageDraw, ImageFont

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.quadtree import Quadtree, Node

def get_min_pos(values, target):
    d = [(target - x)**2 for x in values]
    ## print(values)
    # print('min', referencevalue, min(d))
    return d.index(min(d))

start_time = time.time()

# Define Part Geometry
part_segments = SegmentGroup()

PartPt1 = Point(0, 0, 10)

arcpt1 = Point(2.36, 0, 9.72)
arcpt2 = Point(4.58, 0, 8.89)
arcpt3 = Point(6.55, 0, 7.56)
arcpt4 = Point(8.15, 0, 5.80)
arcpt5 = Point(9.28, 0, 3.72)
arcpt6 = Point(9.9, 0, 1.42)
arcpt7 = Point(9.95, 0, -0.95)
arcpt8 = Point(9.45, 0, -3.27)
arcpt9 = Point(8.41, 0, -5.41)
arcpt10 = Point(6.90, 0, -7.24)

PartPt2 = Point(5, 0, -9)
PartPt3 = Point(9.5, 0, -15.85)
PartPt4 = Point(5.4, 0, -22)

smarcpt1 = Point(4.03, 0, -22.68)
smarcpt2 = Point(3.01, 0, -23.81)
smarcpt3 = Point(2.45, 0, -25.23)
smarcpt4 = Point(2.45, 0, -26.76)
smarcpt5 = Point(3.00, 0, -28.18)
smarcpt6 = Point(4.02, 0, -29.31)

PartPt5 = Point(5.4, 0, -30)
# PartPt6 = Point(5.4, 0, -35)
PartPt7 = Point(5.4, 0, -40)
PartPt8 = Point(13, 0, -45)
PartPt9 = Point(13, 0, -48)
PartPt10 = Point(0, 0, -48)

part_segments.add_segment(Segment(PartPt1, arcpt1))
part_segments.add_segment(Segment(arcpt1, arcpt2))
part_segments.add_segment(Segment(arcpt2, arcpt3))
part_segments.add_segment(Segment(arcpt3, arcpt4))
part_segments.add_segment(Segment(arcpt4, arcpt5))
part_segments.add_segment(Segment(arcpt5, arcpt6))
part_segments.add_segment(Segment(arcpt6, arcpt7))
part_segments.add_segment(Segment(arcpt7, arcpt8))
part_segments.add_segment(Segment(arcpt8, arcpt9))
part_segments.add_segment(Segment(arcpt9, arcpt10))
part_segments.add_segment(Segment(arcpt10, PartPt2))

#part_segments.add_segment(Segment(PartPt1, PartPt2, 0.75))
part_segments.add_segment(Segment(PartPt2, PartPt3))
part_segments.add_segment(Segment(PartPt3, PartPt4))
# part_segments.add_segment(Segment(PartPt4, PartPt5, -0.25))
part_segments.add_segment(Segment(PartPt4, smarcpt1))
part_segments.add_segment(Segment(smarcpt1, smarcpt2))
part_segments.add_segment(Segment(smarcpt2, smarcpt3))
part_segments.add_segment(Segment(smarcpt3, smarcpt4))
part_segments.add_segment(Segment(smarcpt4, smarcpt5))
part_segments.add_segment(Segment(smarcpt5, smarcpt6))
part_segments.add_segment(Segment(smarcpt6, PartPt5))

part_segments.add_segment(Segment(PartPt5, PartPt7))
# part_segments.add_segment(Segment(PartPt6, PartPt7))
part_segments.add_segment(Segment(PartPt7, PartPt8))
part_segments.add_segment(Segment(PartPt8, PartPt9))
part_segments.add_segment(Segment(PartPt9, PartPt10))

# Define stock bounds
stockPt1 = Point(0, 0, 25)
stockPt2 = Point(15, 0, -50)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

# create a 2D Quadtree / SDF for the part geometry
x_min = StockBoundingBox.x_min
x_max = StockBoundingBox.x_max

z_min = StockBoundingBox.z_min
z_max = StockBoundingBox.z_max

print('limits', x_min, x_max, z_min, z_max)

height = StockBoundingBox.x_length()
width = StockBoundingBox.z_length()

edge_length = max(height, width)

# creating new Image object
img = Image.new("RGB", (60 + edge_length * 10, edge_length * 10))

# create rectangle image
img1 = ImageDraw.Draw(img)

# quadtree #

center = Point( edge_length / 2, 0 ,z_min + edge_length / 2)

print('center', center.X, center.Z, edge_length, edge_length)

base_node = Node(center, edge_length, edge_length)
qt = Quadtree(base_node, part_segments, img1)

qt_time = time.time()
print("qt time: ", qt_time - start_time) 

points = qt.query(0.25)
print('offset point qty:', len(points))

for pt in points:
    x = pt.X * 10
    z = (pt.Z + 60)* 10
    shape = [(z, x), (z + 1, x + 1)]  
    img1.rectangle(shape, fill ="#fc0303")

qt_query_time = time.time()
print("qt query time: ", qt_query_time - start_time) 

# quadtree #

sdf_time = time.time()
print("SDF time: ", sdf_time - start_time) 

img.show()

