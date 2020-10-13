from LibLathe.LLBoundBox import BoundBox
from LibLathe.LLCommand import Command
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

    def to_commands(self, part_segment_group, stock, step_over, hSpeed, vSpeed):
        """
        converts segmentgroup to gcode commands
        """

        def previousSegmentConnected(seg, segments):
            ''' returns true if seg is connect to the previous seg '''

            currentIdx = segments.index(seg)
            previousIdx = currentIdx - 1

            if not currentIdx == 0:
                currentStartPt = seg.start
                previousEndPt = segments[previousIdx].end

                if currentStartPt.is_same(previousEndPt):
                    # print('segs are connected')
                    return True

            return False

        def get_min_retract_x(seg, segments, part_segment_group):
            ''' returns the minimum x retract based on the current segments and the part_segments '''
            part_segments = part_segment_group.get_segments()
            currentIdx = segments.index(seg)
            x_values = []

            # get the xmax from the current pass segments
            for idx, segment in enumerate(segments):
                x_values.append(segment.get_extent_max('X'))
                if idx == currentIdx:
                    break

            # get the xmax from the part segments up to the z position of the current segment
            seg_z_max = seg.get_extent_max('Z')
            for part_seg in part_segments:

                part_seg_z_max = part_seg.get_extent_max('Z')
                x_values.append(part_seg.get_extent_max('X'))

                if part_seg_z_max < seg_z_max:
                    break

            min_retract_x = max(x_values, key=abs)
            return min_retract_x

        segments = self.get_segments()

        cmds = []
        # cmd = Path.Command('G17')  #xy plane
        # cmd = Command('(start of section)')
        cmd = Command('G18')  # xz plane
        # cmd = Command('G19')  #yz plane
        cmds.append(cmd)

        for seg in segments:

            min_x_retract = get_min_retract_x(seg, segments, part_segment_group)
            x_retract = min_x_retract - step_over
            min_z_retract = stock.ZMax
            z_retract = min_z_retract + step_over

            # print('min_x_retract:', min_x_retract)

            if segments.index(seg) == 0:
                # params = {'X': seg.start.X, 'Y': 0, 'Z': seg.start.Z + step_over, 'F': hSpeed}
                params = {'X': seg.start.X, 'Y': 0, 'Z': z_retract, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                params = {'X': seg.start.X, 'Y': 0, 'Z': seg.start.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

            if seg.bulge == 0:
                if not previousSegmentConnected(seg, segments):
                    # if edges.index(edge) == 1:
                    pt = seg.start  # edge.valueAt(edge.FirstParameter)
                    params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                    cmd = Command('G0', params)
                    cmds.append(cmd)

                pt = seg.end  # edge.valueAt(edge.LastParameter)
                params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                cmd = Command('G1', params)

            if seg.bulge != 0:
                # TODO: define arctype from bulge sign +/-

                pt1 = seg.start
                pt2 = seg.end
                # print('toPathCommand - bulge', seg.bulge )
                if seg.bulge < 0:
                    arcType = 'G2'
                else:
                    arcType = 'G3'

                cen = seg.get_centre_point().sub(pt1)
                # print('toPathCommand arc cen', seg.get_centre_point().X, seg.get_centre_point().Z)
                params = {'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': hSpeed}
                # print('toPathCommand', params)
                cmd = Command(arcType, params)

            cmds.append(cmd)

            if segments.index(seg) == len(segments) - 1:
                params = {'X': x_retract, 'Y': 0, 'Z': seg.end.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                # params = {'X': x_retract, 'Y': 0, 'Z': segments[0].start.Z + step_over, 'F': hSpeed}
                params = {'X': x_retract, 'Y': 0, 'Z': z_retract, 'F': hSpeed}

                rapid = Command('G0', params)
                cmds.append(rapid)

        return cmds
