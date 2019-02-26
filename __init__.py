########## Lathe Path Macro ##########
# Macro for testing Path lathe features
# Writted by: Dubstar_04
# Date: Jan 2019
# Version: 0.2
#################################
# TODO:
# 1. Generate difference between stock and part 
# 2. Limit diameter of cut
# 3. Limit length of cuts
# 4. Remove grooves
# 5. Overcut at start / end / diameter
# 6. Different feed rates for roughing and cutting
#################################

import math 

def get_angle( pt1, pt2):
    deltaY = pt2.z - pt1.z
    deltaX = pt2.x - pt1.x
    angle = math.degrees(math.atan2(deltaY, deltaX))
    print('angle of the dangle:', angle)
    return angle

def delta(a, b):
    return  a - b
    
def length(P1, P2):
    return math.sqrt((P2.x - P1.x)**2 + (P2.y - P1.y)**2 + (P2.z - P1.z)**2)

def getPathParams(start, shapes, retract_pt):
    #print Path.fromShapes.__doc__
    pathParams = {}
    pathParams['start']=start
    pathParams['shapes'] = shapes
    pathParams['return_end'] = False
    pathParams['arc_plane'] =1
    pathParams['sort_mode'] = 0
    pathParams['min_dist'] =0.0
    pathParams['abscissa'] =3.0
    pathParams['nearest_k'] =3
    pathParams['orientation'] =0 
    pathParams['direction'] = 2
    pathParams['threshold'] =0.0 
    pathParams['retract_axis'] = 0
    pathParams['retraction'] = retract_pt
    pathParams['resume_height'] =0.0 
    pathParams['segmentation'] =0.0 
    pathParams['feedrate'] =0.0
    pathParams['feedrate_v'] =0.0
    pathParams['verbose'] = True
    pathParams['abs_center'] = False
    pathParams['preamble'] = True, 
    pathParams['deflection'] =0.01
    return pathParams

