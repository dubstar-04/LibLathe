from LibLathe.LLBoundBox import BoundBox
from LibLathe.LLPoint import Point


class SegmentGroup:
    '''
    Container Group for segments
    '''
    def __init__(self):
        self.segments = []

    def add_segment(self, segment):
        '''
        Add segment to group
        '''
        self.segments.append(segment)

    def get_segments(self):
        '''
        Return segments of group as a list
        '''
        return self.segments

    def extend(self, segmentGroup):
        '''
        Add segment group to this segmentgroup
        '''
        self.segments.extend(segmentGroup.get_segments())

    def count(self):
        '''
        Return the number of segments in the segmentgroup
        '''
        return len(self.segments)

    def boundbox(self):
        '''
        Return the boundbox for the segmentgroup
        '''
        xvalues = []
        yvalues = []
        zvalues = []

        # collect all points from each segment by direction
        for segment in self.get_segments():
            xvalues.extend(segment.get_all_axis_positions('X'))
            yvalues.extend(segment.get_all_axis_positions('Y'))
            zvalues.extend(segment.get_all_axis_positions('Z'))

        XMin = min(xvalues, key=abs)
        YMin = max(xvalues, key=abs)
        ZMin = min(yvalues, key=abs)
        XMax = max(yvalues, key=abs)
        YMax = min(zvalues, key=abs)
        ZMax = max(zvalues, key=abs)

        pt1 = Point(XMin, YMin, ZMin)
        pt2 = Point(XMax, YMax, ZMax)

        segmentGroupBoundBox = BoundBox(pt1, pt2)

        return segmentGroupBoundBox
