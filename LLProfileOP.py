#import math 
#import LibLathe.LLUtils as utils
import LibLathe.LLBaseOP
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment


class ProfileOP(LibLathe.LLBaseOP.BaseOP):
    
    def generate_path(self):
        '''
        ####################
        # 6. Generate Wires For Remaining Stock
        ####################
        '''
        xmin = self.stock.XMin - self.extra_dia 
        zmax = self.stock.ZMax + self.start_offset            
        
        self.clearing_paths = []
        length = self.stock.ZLength + self.end_offset + self.start_offset 
        width = self.stock.XLength/2 - self.min_dia + self.extra_dia 
        step_over = self.step_over
        line_count = width / step_over
           
        counter = 0
        while counter < line_count:
            xpt = xmin + counter * self.step_over
            pt1 = Point(xpt, 0 , zmax)
            pt2 = Point(xpt , 0 , zmax-length)
            path_line = Segment(pt1, pt2)
              
            roughing_boundary = self.offset_edges[-1]
            
            for seg in roughing_boundary:
                #if roughing_boundary.index(seg) == 0:
                #print(roughing_boundary.index(seg), counter)
                intersect, point = seg.intersect(path_line) 
                if intersect:
                    if type(point) is list:
                        point = pt1.nearest(point)
                    path_line = Segment(pt1, point)
                    #if utils.online(seg, point):
                    #    path_line = Segment(pt1, point)
                        
                        #break
            
            self.clearing_paths.append(path_line)
            counter += 1
 
        #clearing_lines = Part.makeCompound(self.clearing_paths)
        #Part.show(clearing_lines, 'clearing_path')
        






