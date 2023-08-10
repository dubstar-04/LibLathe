"""
LibLathe Offsetting Test
Test creating turning offsets using a signed distance field
"""
# Add LibLathe is in the Python Path
import os
import sys
import math
from bisect import bisect_left

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from PIL import Image, ImageDraw, ImageFont


def isInside(segment_group, point):
    intersections = []
    segment_group_bb = segment_group.boundbox()
    projection_line = Segment(Point(point.X,0,segment_group_bb.z_max + 5), point)
    for seg in segment_group.get_segments():
        intersect, pnt = seg.intersect(projection_line)
        if intersect:
            intersections.append(pnt)

    #print('intersections', len(intersections))

    if (len(intersections) % 2) == 0 and len(intersections) > 0 or len(intersections) == 0:
        # even
        return False
    
    # odd
    return True
    
def closest(segment, point):
    #print('seg start', segment.start.X, segment.start.Z)
    #print('seg end', segment.end.X, segment.end.Z)
    APx = point.X - segment.start.X
    APy = point.Z - segment.start.Z
    ABx = segment.end.X - segment.start.X 
    ABy = segment.end.Z  - segment.start.Z

    magAB2 = ABx * ABx + ABy * ABy
    ABdotAP = ABx * APx + ABy * APy
    t = ABdotAP / magAB2

    # check if the point is < start or > end
    if t > 0 and t < 1:
        x = segment.start.X + ABx * t
        z = segment.start.Z + ABy * t
        pt = Point(x, 0, z)
        # print('pt', pt.Z, pts.Z)
        return pt
    
    if t < 0:
        return segment.start
    if t > 1:
        return segment.end

def get_min_pos(values, target):
    d = [(target - x)**2 for x in values]
    ## print(values)
    # print('min', referencevalue, min(d))
    return d.index(min(d))

# Define Part Geometry
part_segments = SegmentGroup()

PartPt1 = Point(0, 0, 0)
PartPt2 = Point(15, 0, -5)
PartPt3 = Point(15, 0, -15)
PartPt4 = Point(0, 0, -20)

part_segments.add_segment(Segment(PartPt1, PartPt2))
part_segments.add_segment(Segment(PartPt2, PartPt3))
part_segments.add_segment(Segment(PartPt3, PartPt4))

# Define stock bounds
stockPt1 = Point(0, 0, 5)
stockPt2 = Point(25, 0, -25)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

sdf = []

# create a 2D SDF for the part geometry
resolution = 0.1
x_min = StockBoundingBox.x_min
x_max = StockBoundingBox.x_max

z_min = StockBoundingBox.z_min
z_max = StockBoundingBox.z_max

z_pos = z_max
while z_pos >= z_min:
    column = []
    x_pos = x_min
    while x_pos <= x_max:
        # point = Point(16, 0, -4)
        point = Point(x_pos, 0, z_pos)
        inside = isInside(part_segments, point)
        dist_clst_pnt = float('inf')

        for seg in part_segments.get_segments():
            clst = closest(seg, point)
            
            if clst is not None:
                clst_dist = clst.distance_to(point)
                #print('clst_pnt', clst.X, clst.Z, clst_dist)
                dist_clst_pnt = min(clst_dist, dist_clst_pnt)
        
        dist = abs(dist_clst_pnt)
        #print('dist', dist)
        if inside:
            dist = -dist

        column.append(dist)
        x_pos += resolution
    sdf.append(column)
    z_pos -= resolution
# print(sdf)
# print('width', len(sdf), len(sdf[0]))
width = len(sdf)
height = len(sdf[0])

# creating new Image object
img = Image.new("RGB", (width, height))

# create rectangle image
img1 = ImageDraw.Draw(img)

# get the column index closest to target
for target in range(0, 6, 1):
    for idx, column in enumerate(sdf):
        index = get_min_pos(column, target)

        #font = ImageFont.truetype("caladea.ttf", 15)
        #img1.text((idx, index), "1", font=font)

        shape = [(idx, index), (idx + 1, index + 1)]  
        img1.rectangle(shape, fill ="#ffff33")

img.show()
