#from FreeCAD import Vector
#import DraftGeomUtils
#import Part
#import Path
import math 
#import FreeCAD
import LibLathe.LLUtils as utils
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment


class Profile:
    def __init__(self):

        self.stock = None
        self.part = None

        self.offset_edges = []
        self.clearing_paths = []
         
        self.min_dia = 0
        self.extra_dia = 0
        self.start_offset = 0
        self.end_offset = 0
        self.allow_grooving = False
        self.allow_facing = False
        self.step_over = 1.5
        self.finish_passes = 2
        self.hfeed = 100
        self.vfeed = 50

    def set_params(self, params):
        for param in params:
            print(param, params[param])
        pass

    def get_params(self):
        pass

    def get_gcode(self):
        '''
        ####################
        # 1. Get Stock Silhoutte
        ####################
        '''
        print('LathePath - generate_path')
        self.remove_the_groove()
        self.offset_part_outline()
        self.generate_clearing()
        Path = self.generate_gcode()
        #self.clean_up()
        return Path
        
    def remove_the_groove(self):
        '''
        ####################
        # 4. Remove The Groove
        ####################
        '''
        
        if not self.allow_grooving:
            self.part = utils.remove_the_groove(self.part, self.stock.ZMin)
            self.offset_edges.append(self.part)    
        
        #path_profile = Part.makePolygon(profile_points)
       # path_profile = Part.makeCompound(self.part)
        #Part.show(path_profile, 'Final_pass')    
        
 
    def offset_part_outline(self):
        '''
        ####################
        # 5. Offset Part Outline
        ####################
        '''
        f_pass = 1
        while f_pass != self.finish_passes:
            print('fpass', f_pass, self.finish_passes)
            f_pass_geom = utils.offsetPath(self.part, self.step_over * f_pass)  
            self.offset_edges.append(f_pass_geom)
            f_pass += 1
        
        #if len(self.offset_edges):
        #    self.finish_path = []
        #    for path in self.offset_edges:
        #        for edge in path:
        #            self.finish_path.append(edge)
            #offset_profile = Part.makeCompound(finish_path)
            #Part.show(offset_profile, 'finishing_pass')
    
    def generate_clearing(self):
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
         
    def generate_gcode(self):
        '''
        ####################
        # 7. Wires To GCode
        ####################
        '''
        Path = []
        for path in self.offset_edges:   
            finish = utils.toPathCommand(path,  self.step_over, self.hfeed,  self.vfeed)
            Path.append(finish)
        for path in self.clearing_paths: 
            rough = utils.toPathCommand([path],  self.step_over, self.hfeed,  self.vfeed)
            Path.append(rough)

        return Path


                 
    def set_options(self, min_dia, max_dia, start, end, allow_grooving, allow_facing, step_over, finishing_passes):
        self.min_dia = min_dia
        self.extra_dia = max_dia
        self.start_offset = start
        self.end_offset = end
        self.allow_grooving = allow_grooving
        self.allow_facing = allow_facing
        self.step_over = step_over
        self.finish_passes = finishing_passes
        #self.generate_path()
        
    def add_part(self, part_edges):
        #print('Add_part', part_edges)
        self.part = part_edges
        
    def add_stock(self, stock_bb):
        self.stock = stock_bb
        






