"""
LibLathe Offsetting Test
Test creating turning offsets using a signed distance field
"""
# Add LibLathe is in the Python Path
import os
import sys
import math
import time

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from PIL import Image, ImageDraw, ImageFont


def isInside(segment_group, point):
    intersections = 0
    segment_group_bb = segment_group.boundbox()
    projection_line = Segment(Point(point.X,0,segment_group_bb.z_max + 20), point)
    for seg in segment_group.get_segments():

        # stop checking once past the point of interest
        if seg.start.Z < point.Z: #and seg.end.Z < point.Z:
            break

        if round(seg.start.X, 5) <= round(point.X, 5) and round(seg.end.X, 5) <= round(point.X, 5) :
            # print('X poseseses same')
            continue

        intersect, pnt = seg.intersect(projection_line)

        if intersect:
            intersections += len(pnt)



    if intersections % 2 == 0 and intersections > 0 or intersections == 0:
        # even
        return False
    
    # odd
    return True
   
def closestPointOnLine(segment, point):
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
    
def closestPointOnArc(segment, point):

    centerPoint = segment.get_centre_point()
    length = point.distance_to(centerPoint)

    if length == 0:
        return None
    
    radius = segment.get_radius()

    Cx = centerPoint.X + radius * (point.X - centerPoint.X) / length
    Cy = centerPoint.Z + radius * (point.Z - centerPoint.Z) / length
    closest = Point(Cx, 0, Cy)

    #print('calc point', Cx, Cy)

    if segment.point_on_segment(closest):
        #print('return point', Cx, Cy)
        return closest
    # return the nearest end point
    nearest = point.nearest([segment.start, segment.end])
    #print('return nearest point', nearest.X, nearest.Z)
    return nearest
    
    '''
    start_angle = centerPoint.angle_to(segment.start)
    point_angle = centerPoint.angle_to(point)
    end_angle = centerPoint.angle_to(segment.end)

    print('angles', start_angle, point_angle, end_angle)
    
    #if self.bulge > 0:
    if point_angle > start_angle :
        print('pnt greater')
        return segment.start
    '''

    # Point not on arc
    return None

def closest(segment, point):
    if segment.bulge != 0:
        return closestPointOnArc(segment, point)
    else:
        return closestPointOnLine(segment, point)


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
stockPt2 = Point(25, 0, -60)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

sdf = []

# create a 2D SDF for the part geometry
resolution = 0.2
x_min = StockBoundingBox.x_min
x_max = StockBoundingBox.x_max

z_min = StockBoundingBox.z_min
z_max = StockBoundingBox.z_max

print('limits', x_min, x_max, z_min, z_max)

#segment = Segment(PartPt1, PartPt2, 0.75)

#closestPointOnArc(segment, Point(5,0,9))


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

sdf_time = time.time()

print("SDF time: ", sdf_time - start_time) 

width = len(sdf)
height = len(sdf[0])

# creating new Image object
img = Image.new("RGB", (width, height))

# create rectangle image
img1 = ImageDraw.Draw(img)

'''
# get the column index closest to target
for target in range(0, 1, 1):
    for idx, column in enumerate(sdf):
        index = get_min_pos(column, target)

        #font = ImageFont.truetype("caladea.ttf", 15)
        #img1.text((idx, index), "1", font=font)

        shape = [(idx, index), (idx + 1, index + 1)]  
        img1.rectangle(shape, fill ="#ffff33")
'''

target = 0.1
threshold = resolution * 0.5
sdf.reverse()
for z, column in enumerate(sdf):
    for x, row in enumerate(column):
        #print(x, z)
        value = sdf[z][x]
        shape = [(z, x), (z + 1, x + 1)] 
        colour = '#' + '000000'

        if value > 0:
            colour = '#{:02x}{:02x}{:02x}'.format(255, int(value * 10), int(value * 10))
        for i in range(0, 200, 20):
            if value < (target * i) + threshold and value > (target * i) - threshold:
                colour = '#' + '000000'
        
        if value < -1 + threshold and value > -1 - threshold:
            colour = '#' + 'ffffff'
    
        
        img1.rectangle(shape, fill = colour)


'''
# get the column index closest to target
sdf.reverse()

for z, column in enumerate(sdf):
    for x, row in enumerate(column):
        #print(x, z)
        value = sdf[z][x]
        if value < 0:
            shape = [(z, x), (z + 1, x + 1)] 
            colour = '#' + 'ff0303'
            img1.rectangle(shape, fill = colour)

for target in range(1, 6, 1):
    for idx, column in enumerate(sdf):
        index = get_min_pos(column, target)

        #font = ImageFont.truetype("caladea.ttf", 15)
        #img1.text((idx, index), "1", font=font)

        shape = [(idx, index), (idx + 1, index + 1)]  
        img1.rectangle(shape, fill ="#ffff33")
'''

end_time = time.time()

print("Elapsed time: ", end_time - start_time) 

img.show()

