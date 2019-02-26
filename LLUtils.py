import Path
import math 
from LLPoint import Point
from LLSegment import Segment
from LLVector import Vector

def get_tool_cutting_angle():
    return 275   

def remove_the_groove(segments, stock_zmin):

    segs_out = []
    index = 0
    while index < len(segments):
        seg = segments[index]
                   
        if seg.bulge != 0:
            if seg.bulge > 0: 
                seg = Segment(seg.start, seg.end)

            segs_out.append(seg)

        if seg.bulge == 0:
            pt1 = seg.start 
            pt2 = seg.end
            #print('seg angle', segments.index(seg), pt1.angle_to(pt2))
            if pt1.angle_to(pt2) > get_tool_cutting_angle():               
                next_index, pt = find_next_good_edge(segments, index, stock_zmin)
                if next_index == False:
                    seg = Segment(pt1, pt)
                    segs_out.append(seg)
                    break
                if next_index != index: 
                    seg = Segment(pt1, pt)
                    segs_out.append(seg)                  
                    next_pt1 = segments[next_index].start
                    next_pt2 = segments[next_index].end 
                if next_pt1 != pt:
                    seg = Segment(pt1, next_pt2)
                    segs_out.append(seg) 
                    next_index +=1
                            
                index = next_index
                continue
            else:
                segs_out.append(seg)
            
        index += 1 
    return segs_out    

def find_next_good_edge(segments, current_index, stock_zmin):
    index = current_index
    pt1 = segments[index].start
    index += 1    
    while index < len(segments):
        pt2 = segments[index].start       
        if pt1.angle_to(pt2) < get_tool_cutting_angle():
            return index, pt2          
        index += 1
    
    stock_pt =  Point(pt1.X, pt1.Y, stock_zmin)
    seg = Segment(pt1, stock_pt)
    index = current_index
    index += 1
    
    while index < len(segments):
        intersect, point = seg.intersect(segments[index])    
        if intersect:
            print('Utils intersect:', point.X)
            return index, point

        index += 1
    #No solution :(
    print('find_next_good_edge: FAILED')
    return False, stock_pt    
            
def offsetPath(segs, step_over):

    #TODO Sort Edges to ensure they're in order.  See: Part.__sortEdges__()
    nedges = []  

    for i in range(len(segs)):
        seg = segs[i]
        if seg.bulge != 0:

            if seg.bulge > 0:
                vec = Vector().normalise(seg.start, seg.get_centre_point())
                vec2 = Vector().normalise(seg.end, seg.get_centre_point())
                pt = vec.multiply(step_over)
                pt2 = vec2.multiply(step_over)
                new_start = seg.start.add(pt)
                new_end = seg.end.add(pt2)

                new_start.X = new_start.X - step_over
                new_end.X = new_end.X - step_over
                rad = seg.get_radius() - step_over
                #print('offsetPath arc dims', new_start.X, new_start.Z, new_end.X, new_end.Z)
            else:
                vec = Vector().normalise(seg.get_centre_point(), seg.start)
                vec2 = Vector().normalise(seg.get_centre_point(), seg.end)
                pt = vec.multiply(step_over)
                pt2 = vec2.multiply(step_over)
                new_start = pt.add(seg.start)
                new_end = pt2.add(seg.end)
                rad = seg.get_radius() + step_over #seg.get_centre_point().distance_to(new_start)
           
            nedge = Segment(new_start, new_end)

            
            if seg.bulge < 0:
                rad = 0 - rad
            nedge.set_bulge_from_radius(rad)

        if seg.bulge == 0:         
            vec = Vector().normalise(seg.start, seg.end)
            vec = vec.rotate_x(-1.570796)
            pt = vec.multiply(step_over)
            nedge = Segment(pt.add(seg.start), pt.add(seg.end))
              
        nedges.append(nedge)
        
    return join_edges(nedges)          
        
def join_edges(segments):

    segments_out = []
    
    for i in range(len(segments)):

        pt1 = segments[i].start
        pt2 = segments[i].end 

        seg1 = segments[i]    
        if i !=0:
            seg1 = segments[i-1]
            intersect, pt = seg1.intersect(segments[i], extend=True)
            if intersect:
                if type(pt) is list:
                    pt = pt1.nearest(pt)
                pt1 = pt         
        
        if i != len(segments)-1:      
            seg2 = segments[i+1]
            intersect2, pt = seg2.intersect(segments[i], extend=True) 
            if intersect2:
                print('intersect2')
                if type(pt) is list:
                    print('join_edges type of', type(pt))
                    pt = pt2.nearest(pt)
                pt2 = pt 

            print('join_edges', i, pt1, pt2, pt2.X, pt2.Z) 
                         

        if pt1 and pt2:
            if segments[i].bulge != 0:               
                nseg = Segment(pt1, pt2)
                rad = segments[i].get_centre_point().distance_to(pt1)
                if segments[i].bulge < 0:
                    rad = 0 - rad
                nseg.set_bulge_from_radius(rad)
                segments_out.append(nseg) 
            else:
                segments_out.append(Segment(pt1, pt2))
        else:
            #No Intersections found. Return the segment in its current state
            print('join_edges - No Intersection found for index:', i)
            segments_out.append(segments[i])

    return segments_out
    
def toPathCommand(segments, step_over, hSpeed, vSpeed):

    cmds = []
    #cmd = Path.Command('G17')  #xy plane
    cmd = Path.Command('G18')   #xz plane
    #cmd = Path.Command('G19')  #yz plane
    cmds.append(cmd)


    for seg in segments:
       
        if segments.index(seg) == 0:
            params = {'X': seg.start.X, 'Y': 0, 'Z': seg.start.Z + step_over, 'F': hSpeed}
            rapid =  Path.Command('G0', params)
            cmds.append(rapid)    

            params = {'X': seg.start.X, 'Y': 0, 'Z': seg.start.Z, 'F': hSpeed}
            rapid =  Path.Command('G0', params)
            cmds.append(rapid)  
        
        if seg.bulge == 0:
            #if edges.index(edge) == 1:
            pt = seg.start #edge.valueAt(edge.FirstParameter) 
            params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
            cmd =  [Path.Command('G0', params)]
            cmds.append(cmd)
            
            pt = seg.end #edge.valueAt(edge.LastParameter)
            params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
            cmd =  Path.Command('G1', params)

        if seg.bulge != 0:
            #TODO: define arctype from bulge sign +/-

            pt1 = seg.start
            pt2 = seg.end 
            #print('toPathCommand - bulge', seg.bulge )
            if seg.bulge < 0:
                arcType = 'G2' 
            else:
                arcType = 'G3'
                
            cen = seg.get_centre_point().sub(pt1) 
            #print('toPathCommand arc cen', seg.get_centre_point().X, seg.get_centre_point().Z)          
            params = ({'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': hSpeed})
            #print('toPathCommand', params)
            cmd =  Path.Command(arcType, params)

        cmds.append(cmd)

        if segments.index(seg) == len(segments)-1:
            params = {'X': seg.end.X - step_over, 'Y': 0, 'Z': seg.end.Z, 'F': hSpeed}
            rapid =  Path.Command('G0', params)
            cmds.append(rapid)

            params = {'X': seg.end.X - step_over, 'Y': 0, 'Z': segments[0].start.Z + step_over, 'F': hSpeed}
            rapid =  Path.Command('G0', params)
            cmds.append(rapid)
           
    return cmds
