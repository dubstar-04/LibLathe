import math

from liblathe.boundbox import BoundBox
from liblathe.command import Command
from liblathe.point import Point
from liblathe.segment import Segment


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

        x_min = min(xvalues, key=abs)
        x_max = max(xvalues, key=abs)
        y_min = min(yvalues, key=abs)
        y_max = max(yvalues, key=abs)
        z_min = min(zvalues, key=abs)
        z_max = max(zvalues, key=abs)

        pt1 = Point(x_min, y_min, z_min)
        pt2 = Point(x_max, y_max, z_max)

        segmentgroupBoundBox = BoundBox(pt1, pt2)

        return segmentgroupBoundBox

    def z_at_x(self, x):
        """get the z value at the first intersection at the given x position"""
        boundbox = self.boundbox()
        offset = boundbox.z_length()
        start_pt = Point(x, 0, boundbox.z_max + offset)
        end_pt = Point(x, 0, boundbox.z_min - offset)

        line_segment = Segment(start_pt, end_pt)
        for segment in self.get_segments():
            intersect, pts = segment.intersect(line_segment)
            if intersect:
                return pts[0].Z
        return None

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
                    if type(pt) is list:
                        pt = pt2.nearest(pt)
                    pt2 = pt

            if pt1 and pt2:
                if segments[i].bulge != 0:
                    rad = segments[i].get_centre_point().distance_to(pt1)
                    nseg = Segment(pt1, pt2)
                    nseg.derive_bulge(segments[i], rad)
                    segmentgroupOut.add_segment(nseg)
                else:
                    segmentgroupOut.add_segment(Segment(pt1, pt2))
            else:
                # No Intersections found. Return the segment in its current state
                segmentgroupOut.add_segment(segments[i])

        self.segments = segmentgroupOut.get_segments()
        self.clean_offset_path()

    def merge_segments(self):
        """merge adjacent line segments"""
        for i in range(len(self.segments)):
            if i + 1 < len(self.segments):
                if self.segments[i].get_rotation() == self.segments[i + 1].get_rotation():
                    if self.segments[i].bulge == 0 and self.segments[i + 1].bulge == 0:
                        self.segments[i].end = self.segments[i + 1].end
                        self.segments.pop(i + 1)
                        # call merge segments again
                        self.merge_segments()

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
                            self.segments[index].derive_bulge(self.segments[index])

                        self.segments[i].start = pt
                        if self.segments[i].bulge:
                            self.segments[i].derive_bulge(self.segments[i])
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

        # get the x_max from the current pass segments
        for idx, seg in enumerate(self.segments):
            x_values.append(seg.get_extent_max('X'))
            if idx == currentIdx:
                break

        # get the x_max from the part segments up to the z position of the current segment
        seg_z_max = segment.get_extent_max('Z')
        for part_seg in part_segments:

            part_seg_z_max = part_seg.get_extent_max('Z')
            x_values.append(part_seg.get_extent_max('X'))

            if part_seg_z_max < seg_z_max:
                break

        min_retract_x = max(x_values, key=abs)
        return min_retract_x

    def to_commands(self, part_segment_group, stock, step_over, finish_passes, hSpeed, vSpeed, invert_x=True):
        """converts segmentgroup to gcode commands"""

        def get_pos(pnt):
            x = pnt.X
            y = pnt.Y
            z = pnt.Z

            if invert_x:
                x = 0 - x

            return Point(x, y, z)

        def get_arc_type(bulge):
            if bulge > 0:
                arcType = 'G2' if invert_x else 'G3'
            else:
                arcType = 'G3' if invert_x else 'G2'

            return arcType

        segments = self.get_segments()

        cmds = []
        # TODO: Move the G18 to a PATH Class? it doesn't need to be added to every segment group
        cmd = Command('G18')  # xz plane
        cmds.append(cmd)

        for seg in segments:
            min_x_retract = self.get_min_retract_x(seg, part_segment_group)
            x_retract = min_x_retract - step_over * finish_passes
            z_retract = segments[0].start.Z

            if invert_x:
                x_retract = 0 - x_retract

            # rapid to the start of the segmentgroup
            if segments.index(seg) == 0:
                pt = get_pos(seg.start)
                params = {'X': pt.X, 'Y': 0, 'Z': pt.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

            # handle line segments
            if seg.bulge == 0:
                # handle unconnected segments
                if not self.previous_segment_connected(seg) and segments.index(seg) != 0:
                    pt = get_pos(seg.start)
                    # rapid to the x_min
                    params = {'X': x_retract, 'Y': pt.Y, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid at x_min to the start of the segment
                    params = {'X': x_retract, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid to the start of the start of the cutting move
                    params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                    cmd = Command('G0', params)
                    cmds.append(cmd)
                # perform the cutting
                pt = get_pos(seg.end)
                params = {'X': pt.X, 'Y': pt.Y, 'Z': pt.Z, 'F': hSpeed}
                cmd = Command('G1', params)
                cmds.append(cmd)
            # handle arc segments
            if seg.bulge != 0:
                pt1 = get_pos(seg.start)
                pt2 = get_pos(seg.end)
                # set the arc direction
                arcType = get_arc_type(seg.bulge)

                # set the arc parameters
                cen = get_pos(seg.get_centre_point()).sub(pt1)
                params = {'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': hSpeed}
                cmd = Command(arcType, params)
                cmds.append(cmd)

            # handle the lead out at the end of the segmentgroup
            if segments.index(seg) == len(segments) - 1:
                pt = get_pos(seg.end)
                params = {'X': x_retract, 'Y': 0, 'Z': pt.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                params = {'X': x_retract, 'Y': 0, 'Z': z_retract, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

        return cmds

    def offset_path(self, step_over):
        # TODO Sort Edges to ensure they're in order.

        if step_over == 0:
            return self

        segs = self.get_segments()
        segmentgroup = SegmentGroup()

        for i in range(len(segs)):
            seg = segs[i]
            if seg.bulge != 0:

                if seg.bulge > 0:
                    # get normal from end point to centre
                    start_normal = seg.start.normalise_to(seg.get_centre_point())
                    end_normal = seg.end.normalise_to(seg.get_centre_point())
                    # get point in the direction of the normal with magnitude of step_over
                    pt1 = start_normal.multiply(step_over)
                    pt2 = end_normal.multiply(step_over)
                    # get the new start and end points
                    new_start = seg.start.add(pt1)
                    new_end = seg.end.add(pt2)
                    rad = seg.get_radius() - step_over
                else:
                    # get normal from the centre to the end points
                    start_normal = seg.get_centre_point().normalise_to(seg.start)
                    end_normal = seg.get_centre_point().normalise_to(seg.end)
                    # get point in the direction of the normal with magnitude of step_over
                    pt1 = start_normal.multiply(step_over)
                    pt2 = end_normal.multiply(step_over)
                    # get the new start and end points
                    new_start = pt1.add(seg.start)
                    new_end = pt2.add(seg.end)
                    rad = seg.get_radius() + step_over

                segment = Segment(new_start, new_end)
                segment.derive_bulge(seg, rad)

            if seg.bulge == 0:
                normal = seg.start.normalise_to(seg.end).rotate(-90)
                pt = normal.multiply(step_over)
                segment = Segment(pt.add(seg.start), pt.add(seg.end))

            segmentgroup.add_segment(segment)

        segmentgroup.join_segments()
        return segmentgroup

    def remove_the_groove(self, stock_z_min, tool, allow_grooving=False):
        segments = self.get_segments()
        segs_out = SegmentGroup()
        index = 0

        while index < len(segments):
            seg = segments[index]
            next_index = False
            pt1 = seg.start
            pt2 = seg.end
            pt = None

            # TO DO: Tidy this mess

            if seg.bulge > 0:
                segAng = round(math.degrees(seg.get_angle()), 5)
                # get angle tangent to the start point
                startPtAng = round(pt1.angle_to(seg.get_centre_point()) - 90, 5)
                if startPtAng >= tool.get_tool_cutting_angle():
                    if startPtAng + segAng <= 270:
                        segs_out.add_segment(seg)
                else:
                    ang = tool.get_tool_cutting_angle()
                    # calculate the length required to project the point to the centreline
                    length = abs(pt1.X / math.cos(math.radians(ang - 90)))
                    proj_pt = pt1.project(ang, length)
                    projseg = Segment(pt1, proj_pt)
                    intersect, pts = projseg.intersect(segments[index])
                    if intersect and allow_grooving:
                        # add the intersecting line to the segment_group
                        new_seg = Segment(pt1, pts[0])
                        segs_out.add_segment(new_seg)
                        # add the remainder of the arc to the segment_group
                        remaining_seg = Segment(pts[0], pt2)
                        remaining_seg.derive_bulge(seg)
                        segs_out.add_segment(remaining_seg)
                    else:
                        if seg.start.angle_to(seg.end) <= 180:
                            seg = Segment(pt1, pt2)
                            segs_out.add_segment(seg)
                        else:
                            pt = seg.start
                            next_index, pt = self.find_next_good_edge(index, stock_z_min, tool, allow_grooving, pt)

            if seg.bulge < 0:
                # Limit the arc movement to the X extents or the tangent at the max tool angle if allow_grooving
                angle_limit = 270 if allow_grooving is False else tool.get_tool_cutting_angle() + 90
                if seg.get_centre_point().angle_to(pt2) >= angle_limit:
                    segs_out.add_segment(seg)
                else:
                    rad = seg.get_radius()
                    if not allow_grooving:
                        # define a point vertically down on the x axis.
                        x = seg.get_centre_point().X - rad
                        y = seg.get_centre_point().Y
                        z = seg.get_centre_point().Z
                        pt = Point(x, y, z)
                    else:
                        # project a point from the centre of the arc along the angle limit to the radius
                        pt = seg.get_centre_point().project(angle_limit, rad)

                    nseg = Segment(pt1, pt)
                    nseg.derive_bulge(seg, rad)
                    segs_out.add_segment(nseg)

                    pt1 = pt
                    next_index, pt = self.find_next_good_edge(index, stock_z_min, tool, allow_grooving, pt)

            elif seg.bulge == 0:
                if pt1.angle_to(pt2) < tool.get_tool_cutting_angle():
                    next_index, pt = self.find_next_good_edge(index, stock_z_min, tool, allow_grooving)
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
                seg.derive_bulge(segments[next_index])
                segs_out.add_segment(seg)

                next_index += 1
                index = next_index
                continue

            index += 1
        segs_out.merge_segments()
        return segs_out

    def find_next_good_edge(self, current_index, stock_z_min, tool, allow_grooving, pt=None):
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
                length = abs(pt1.X / math.cos(math.radians(ang - 90)))
                pt2 = pt1.project(ang, length)
            else:
                pt2 = Point(pt1.X, pt1.Y, stock_z_min)

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

        stock_pt = Point(pt1.X, pt1.Y, stock_z_min)
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
