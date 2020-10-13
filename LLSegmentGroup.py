from LibLathe.LLBoundBox import BoundBox
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment


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

    def join_segments(self):
        """
        join segments of the segmentgroup
        """

        segments = self.get_segments()
        segmentGroupOut = SegmentGroup()

        for i in range(len(segments)):

            pt1 = segments[i].start
            pt2 = segments[i].end

            seg1 = segments[i]
            if i != 0:
                seg1 = segments[i - 1]
                intersect, pt = seg1.intersect(segments[i], extend=True)
                if intersect:
                    if type(pt) is list:
                        pt = pt1.nearest(pt)
                    pt1 = pt

            if i != len(segments) - 1:
                seg2 = segments[i + 1]
                intersect2, pt = seg2.intersect(segments[i], extend=True)
                if intersect2:
                    # print('intersect2')
                    if type(pt) is list:
                        # print('join_segments type of', type(pt))
                        pt = pt2.nearest(pt)
                    pt2 = pt

                    # print('join_segments', i, pt1, pt2, pt2.X, pt2.Z)

            if pt1 and pt2:
                if segments[i].bulge != 0:
                    nseg = Segment(pt1, pt2)
                    rad = segments[i].get_centre_point().distance_to(pt1)
                    if segments[i].bulge < 0:
                        rad = 0 - rad
                    nseg.set_bulge_from_radius(rad)
                    segmentGroupOut.add_segment(nseg)
                else:
                    segmentGroupOut.add_segment(Segment(pt1, pt2))
            else:
                # No Intersections found. Return the segment in its current state
                # print('join_segments - No Intersection found for index:', i)
                segmentGroupOut.add_segment(segments[i])

        self.segments = segmentGroupOut.get_segments()
