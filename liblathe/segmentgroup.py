import math

from liblathe.boundbox import BoundBox
from liblathe.command import Command
from liblathe.point import Point
from liblathe.segment import Segment
from liblathe.vector import Vector


class SegmentGroup:
    """Container Group for segments"""

    def __init__(self):
        self.segments = []

    def add_segment(self, segment):
        """Add segment to group"""

        self.segments.append(segment)

    def get_segments(self):
        """Return segments of group as a list"""

        return self.segments

    def extend(self, segmentgroup):
        """Add segment group to this segmentgroup"""

        self.segments.extend(segmentgroup.get_segments())

    def count(self):
        """Return the number of segments in the segmentgroup"""

        return len(self.segments)

    def boundbox(self):
        """Return the boundbox for the segmentgroup"""

        xvalues = []
        yvalues = []
        zvalues = []

        # collect all points from each segment by direction
        for segment in self.get_segments():
            xvalues.extend(segment.get_all_axis_positions('X'))
            yvalues.extend(segment.get_all_axis_positions('Y'))
            zvalues.extend(segment.get_all_axis_positions('Z'))

        XMin = min(xvalues, key=abs)
        XMax = max(xvalues, key=abs)
        YMin = min(yvalues, key=abs)
        YMax = max(yvalues, key=abs)
        ZMin = min(zvalues, key=abs)
        ZMax = max(zvalues, key=abs)

        pt1 = Point(XMin, YMin, ZMin)
        pt2 = Point(XMax, YMax, ZMax)

        segmentgroupBoundBox = BoundBox(pt1, pt2)

        return segmentgroupBoundBox

    def join_segments(self):
        """join segments of the segmentgroup"""

        segments = self.get_segments()
        segmentgroupOut = SegmentGroup()

        for i in range(len(segments)):

            pt1 = segments[i].start
            pt2 = segments[i].end

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
                    segmentgroupOut.add_segment(nseg)
                else:
                    segmentgroupOut.add_segment(Segment(pt1, pt2))
            else:
                # No Intersections found. Return the segment in its current state
                # print('join_segments - No Intersection found for index:', i)
                segmentgroupOut.add_segment(segments[i])

        self.segments = segmentgroupOut.get_segments()
        self.clean_offset_path()

    def clean_offset_path(self, index=0):
        """
        remove any self intersecting features from the path.
        index is the segment to evaluate
        """
        segments = self.get_segments()
        if index + 1 < len(segments):
            for i in range(len(segments) - 1, index, -1):
                if i != index:
                    if segments[index].end.is_same(segments[i].start):
                        continue

                    intersect, pt = segments[index].intersect(segments[i])
                    if intersect:
                        if type(pt) is list:
                            pt = pt[0]

                        self.segments[index].end = pt
                        if self.segments[index].bulge:
                            rad = self.segments[index].get_radius()
                            if self.segments[index].bulge < 0:
                                rad = 0 - rad
                            self.segments[index].set_bulge_from_radius(rad)

                        self.segments[i].start = pt
                        if self.segments[i].bulge:
                            rad = self.segments[i].get_radius()
                            if self.segments[i].bulge < 0:
                                rad = 0 - rad
                            self.segments[i].set_bulge_from_radius(rad)

                        if i != index + 1:
                            del self.segments[index + 1:i]

                        break

            if index < self.count():
                # run again with the next segment
                self.clean_offset_path(index + 1)

    def previous_segment_connected(self, segment):
        """returns bool if segment is connect to the previous segment"""

        currentIdx = self.segments.index(segment)
        previousIdx = currentIdx - 1

        if not currentIdx == 0:
            currentStartPt = segment.start
            previousEndPt = self.segments[previousIdx].end

            if currentStartPt.is_same(previousEndPt):
                return True

        return False

    def get_min_retract_x(self, segment, part_segment_group):
        """ returns the minimum x retract based on the current segments and the part_segments """

        part_segments = part_segment_group.get_segments()
        currentIdx = self.segments.index(segment)
        x_values = []

        # get the xmax from the current pass segments
        for idx, seg in enumerate(self.segments):
            x_values.append(seg.get_extent_max('X'))
            if idx == currentIdx:
                break

        # get the xmax from the part segments up to the z position of the current segment
        seg_z_max = segment.get_extent_max('Z')
        for part_seg in part_segments:

            part_seg_z_max = part_seg.get_extent_max('Z')
            x_values.append(part_seg.get_extent_max('X'))

            if part_seg_z_max < seg_z_max:
                break

        min_retract_x = max(x_values, key=abs)
        return min_retract_x

    def to_commands(self, part_segment_group, stock, step_over, finish_passes, hSpeed, vSpeed):
        """converts segmentgroup to gcode commands"""

        segments = self.get_segments()

        cmds = []
        # TODO: Move the G18 to a PATH Class? it doent need to be added to every segment group
        cmd = Command('G18')  # xz plane
        cmds.append(cmd)

        for seg in segments:
            min_x_retract = self.get_min_retract_x(seg, part_segment_group)
            x_retract = min_x_retract - step_over * finish_passes
            min_z_retract = stock.ZMax
            z_retract = min_z_retract + step_over

            print('min_x_retract:', min_x_retract)

            # rapid to the start of the segmentgroup
            if segments.index(seg) == 0:

                params = {'X': seg.start.X, 'Y': 0, 'Z': z_retract, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                params = {'X': seg.start.X, 'Y': 0, 'Z': seg.start.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

            # handle line segments
            if seg.bulge == 0:
                # handle unconnected segments
                if not self.previous_segment_connected(seg):
                    pt = seg.start
                    # rapid to the xmin
                    params = {'X': x_retract, 'Y': pt.Y, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid at xmin to the start of te segment
                    params = {'X': x_retract, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid to the start of the start of the cutting move
                    params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                    cmd = Command('G0', params)
                    cmds.append(cmd)
                # perform the cutting
                pt = seg.end
                params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                cmd = Command('G1', params)
                cmds.append(cmd)
            # handle arc segments
            if seg.bulge != 0:
                pt1 = seg.start
                pt2 = seg.end
                # set the arc direction
                if seg.bulge < 0:
                    arcType = 'G2'
                else:
                    arcType = 'G3'
                # set the arc parameters
                cen = seg.get_centre_point().sub(pt1)
                params = {'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': hSpeed}
                cmd = Command(arcType, params)
                cmds.append(cmd)

            # handle the lead out at the end of the segmentgroup
            if segments.index(seg) == len(segments) - 1:
                params = {'X': x_retract, 'Y': 0, 'Z': seg.end.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                params = {'X': x_retract, 'Y': 0, 'Z': z_retract, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

        return cmds

    def offsetPath(self, step_over):
        # TODO Sort Edges to ensure they're in order.
        # nedges = []
        segs = self.get_segments()
        segmentgroup = SegmentGroup()

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
                    # print('offsetPath arc dims', new_start.X, new_start.Z, new_end.X, new_end.Z)
                else:
                    vec = Vector().normalise(seg.get_centre_point(), seg.start)
                    vec2 = Vector().normalise(seg.get_centre_point(), seg.end)
                    pt = vec.multiply(step_over)
                    pt2 = vec2.multiply(step_over)
                    new_start = pt.add(seg.start)
                    new_end = pt2.add(seg.end)
                    rad = seg.get_radius() + step_over  # seg.get_centre_point().distance_to(new_start)

                segment = Segment(new_start, new_end)

                if seg.bulge < 0:
                    rad = 0 - rad
                segment.set_bulge_from_radius(rad)

            if seg.bulge == 0:
                vec = Vector().normalise(seg.start, seg.end)
                vec = vec.rotate_x(-1.570796)
                pt = vec.multiply(step_over)
                segment = Segment(pt.add(seg.start), pt.add(seg.end))

            segmentgroup.add_segment(segment)

        segmentgroup.join_segments()
        return segmentgroup

    def remove_the_groove(self, stock_zmin, tool, allow_grooving=False):
        segments = self.get_segments()
        segs_out = SegmentGroup()
        index = 0

        while index < len(segments):
            seg = segments[index]
            next_index = False
            pt1 = seg.start
            pt2 = seg.end
            pt = None

            if seg.bulge != 0:
                print('arc segment')
                if seg.bulge > 0:
                    # TODO: handle segments with a positive bulge
                    seg = Segment(pt1, pt2)
                    segs_out.add_segment(seg)
                if seg.bulge < 0:
                    # Limit the arc movement to the X extents or the tangent at the max tool angle if allow_grooving
                    angle_limit = 180 if allow_grooving is False else tool.get_tool_cutting_angle() - 90
                    if seg.get_centre_point().angle_to(pt2) <= angle_limit:
                        segs_out.add_segment(seg)
                    else:
                        rad = seg.get_radius()
                        if not allow_grooving:
                            x = seg.get_centre_point().X - rad
                            y = seg.get_centre_point().Y
                            z = seg.get_centre_point().Z
                            pt = Point(x, y, z)
                        else:
                            pt = seg.get_centre_point().project(angle_limit, rad)

                        if seg.bulge < 0:
                            rad = 0 - rad

                        seg = Segment(pt1, pt)
                        seg.set_bulge_from_radius(rad)
                        segs_out.add_segment(seg)

                        pt1 = pt
                        next_index, pt = self.find_next_good_edge(index, stock_zmin, tool, allow_grooving, pt)

            elif seg.bulge == 0:
                print('line segment')
                if pt1.angle_to(pt2) > tool.get_tool_cutting_angle():
                    next_index, pt = self.find_next_good_edge(index, stock_zmin, tool, allow_grooving)
                else:
                    segs_out.add_segment(seg)

            if next_index is False and pt is not None:
                seg = Segment(pt1, pt)
                segs_out.add_segment(seg)
                break
            if next_index is not False and next_index != index:
                seg = Segment(pt1, pt)
                segs_out.add_segment(seg)
                next_pt1 = pt
                next_pt2 = segments[next_index].end
                seg = Segment(next_pt1, next_pt2)
                segs_out.add_segment(seg)
                next_index += 1
                index = next_index
                continue

            index += 1
        return segs_out

    def find_next_good_edge(self, current_index, stock_zmin, tool, allow_grooving, pt=None):
        segments = self.get_segments()
        index = current_index
        if pt is None:
            pt1 = segments[index].start
        else:
            pt1 = pt

        index += 1
        while index < len(segments):

            if allow_grooving:
                # create a new point at the max angle from pt1
                ang = tool.get_tool_cutting_angle()
                # calculate the length required to project the point to the centreline
                length = abs(pt1.X / math.cos(math.radians(360 - ang)))
                pt2 = pt1.project(ang, length)
            else:
                pt2 = Point(pt1.X, pt1.Y, stock_zmin)

            # create a new projected segment
            seg = Segment(pt1, pt2)

            # loop through the remaining segments and see if the projected segments
            idx = index
            while idx < len(segments):
                intersect, pts = seg.intersect(segments[idx])
                if intersect:
                    return idx, pts[0]
                idx += 1
            index += 1

        stock_pt = Point(pt1.X, pt1.Y, stock_zmin)
        seg = Segment(pt1, stock_pt)
        index = current_index
        index += 1

        while index < len(segments):
            intersect, pts = seg.intersect(segments[index])
            if intersect:
                return index, pts[0]

            index += 1
        # No solution :(
        return False, stock_pt
