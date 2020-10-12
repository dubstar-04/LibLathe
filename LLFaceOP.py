import math

import LibLathe.LLBaseOP
import LibLathe.LLUtils as utils
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment
from LibLathe.LLSegmentGroup import SegmentGroup


class FaceOP(LibLathe.LLBaseOP.BaseOP):

    def generate_path(self):
        '''
        Generate the path for the profile operation
        '''
        xmin = self.stock.XMin - self.extra_dia
        xmax = 0 - self.min_dia
        zmax = self.stock.ZMax + self.start_offset

        self.clearing_paths = []
        length = zmax - self.part.ZMax
        step_over = self.step_over
        line_count = math.ceil(length / step_over)
        zstart = self.part.ZMax + step_over * line_count

        # build list of segments
        segmentGroup = SegmentGroup()

        counter = 0
        while counter < line_count + 1:
            zpt = zstart - counter * self.step_over
            pt1 = Point(xmin, 0, zpt)
            pt2 = Point(xmax, 0, zpt)
            path_line = Segment(pt1, pt2)
            seg = path_line
            segmentGroup.add_segment(seg)
            counter += 1

        self.clearing_paths.append(segmentGroup)

    def generate_gcode(self):
        '''
        Generate Gcode for the op segments
        '''
        Path = []
        for segmentGroup in self.clearing_paths:
            rough = utils.toPathCommand(self.part_segment_group, segmentGroup, self.stock, self.step_over, self.hfeed,
                                        self.vfeed)
            Path.append(rough)

        return Path
