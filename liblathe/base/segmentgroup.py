import math
import time

from liblathe.base.boundbox import BoundBox
from liblathe.base.command import Command
from liblathe.base.point import Point
from liblathe.base.segment import Segment

class SegmentGroup:
    """Container Group for segments"""

    def __init__(self):
        self.segments = []

    def add_segment(self, segment):
        """Add segment to group"""

        self.segments.append(segment)

    def insert_segment(self, segment, position):
        """Insert segment into group at position"""
        self.segments.insert(position, segment)

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
            bb = segment.get_boundbox()
            xvalues.extend([bb.x_min, bb.x_max])
            yvalues.extend([bb.y_min, bb.y_max])
            zvalues.extend([bb.z_min, bb.z_max])

        x_min = min(xvalues)
        x_max = max(xvalues)
        y_min = min(yvalues)
        y_max = max(yvalues)
        z_min = min(zvalues)
        z_max = max(zvalues)

        pt1 = Point(x_min, y_min, z_min)
        pt2 = Point(x_max, y_max, z_max)

        segmentgroupBoundBox = BoundBox(pt1, pt2)

        return segmentgroupBoundBox
    
    def intersects_group(self, segment_group):
        """check if the segment_group intersects self"""
        for segment in segment_group.get_segments():
            for seg in self.segments:
                intersect, point = segment.intersect(seg)
                if intersect:
                    return True
        return False

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
            x_values.extend([seg.get_boundbox().x_min, seg.get_boundbox().x_max])
            if idx == currentIdx:
                break

        # get the x_max from the part segments up to the z position of the current segment
        seg_z_max = segment.get_boundbox().z_max
        for part_seg in part_segments:

            part_seg_z_max = part_seg.get_boundbox().z_max
            x_values.extend([part_seg.get_boundbox().x_min, part_seg.get_boundbox().x_max])

            if part_seg_z_max < seg_z_max:
                break

        min_retract_x = max(x_values, key=abs)
        return min_retract_x

    def to_commands(self, part_segment_group, stock, step_over, finish_passes, hSpeed, vSpeed):
        """converts segmentgroup to gcode commands"""

        def get_pos(pnt):
            x = pnt.X
            y = pnt.Y
            z = pnt.Z

            return Point(x, y, z)

        def get_arc_type(bulge):
            if bulge > 0:
                arcType = 'G3'
            else:
                arcType = 'G2'

            return arcType

        segments = self.get_segments()

        cmds = []
        # TODO: Move the G18 to a PATH Class? it doesn't need to be added to every segment group
        cmd = Command('G18')  # xz plane
        cmds.append(cmd)

        for seg in segments:
            min_x_retract = self.get_min_retract_x(seg, part_segment_group)
            x_retract = min_x_retract + step_over * finish_passes
            z_retract = segments[0].start.Z

            # rapid to the start of the segmentgroup
            if segments.index(seg) == 0:
                pt = get_pos(seg.start)
                params = {'X': pt.X, 'Z': pt.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

            # handle line segments
            if seg.bulge == 0:
                # handle unconnected segments
                if not self.previous_segment_connected(seg) and segments.index(seg) != 0:
                    pt = get_pos(seg.start)
                    # rapid to the x_max
                    params = {'X': x_retract, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid at x_max to the start of the segment
                    params = {'X': x_retract, 'Z': pt.Z, 'F': hSpeed}
                    rapid = Command('G0', params)
                    cmds.append(rapid)
                    # rapid to the start of the start of the cutting move
                    params = {'X': pt.X, 'Z': pt.Z, 'F': hSpeed}
                    cmd = Command('G0', params)
                    cmds.append(cmd)
                # perform the cutting
                pt = get_pos(seg.end)
                params = {'X': pt.X, 'Z': pt.Z, 'F': hSpeed}
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
                #TODO: Remove the F parameter from rapid moves
                params = {'X': x_retract, 'Z': pt.Z, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

                params = {'X': x_retract, 'Z': z_retract, 'F': hSpeed}
                rapid = Command('G0', params)
                cmds.append(rapid)

        return cmds

    def offset_path(self, step_over):
        """Create an offset segmentgroup by the distance of step_over"""
        # TODO Sort Edges to ensure they're in order.

        if step_over == 0:
            return self

        segs = self.get_segments()
        segmentgroup = SegmentGroup()

        for seg in segs:
            segment = seg.offset(step_over)

            if segment:
                segmentgroup.add_segment(segment)

        # TODO: create arcs at the intersections between segments, radius needs to be matched to the selected tool

        segmentgroup.join_segments()
        segmentgroup.validate()
        return segmentgroup

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
                    #rad = segments[i].get_centre_point().distance_to(pt1)
                    nseg = Segment(pt1, pt2)
                    ang = segments[i].angle_from_points(nseg.start, nseg.end)
                    nseg.set_bulge(ang)
                    # nseg.derive_bulge(segments[i], rad)
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

                        angle = self.segments[index].angle_from_points(self.segments[index].start, pt)
                        self.segments[index].end = pt
                        if self.segments[index].bulge:
                            self.segments[index].set_bulge(angle)

                        angle = self.segments[i].angle_from_points(pt, self.segments[i].end)
                        self.segments[i].start = pt
                        if self.segments[i].bulge != 0:
                            self.segments[i].set_bulge(angle)
                            #self.segments[i].derive_bulge(self.segments[i])
                        if i != index + 1:
                            del self.segments[index + 1:i]

                        break

            if index < self.count():
                # run again with the next segment
                self.clean_offset_path(index + 1)

    def defeature(self, stock, tool, allow_grooving=False):
        """Defeature the segment group. Remove features that cannot be turned. e.g. undercuts / grooves"""

        x_min = 0
        x_max = self.boundbox().x_max + 1
        z_min = stock.z_min
        z_max = stock.z_max
        resolution = 0.01
        points = []
        # get elapsed time reference
        start = time.time()

        z_pos = z_max
        while z_pos > z_min:
            # test for intersection at z with a single segment
            test_segment = Segment(Point(x_max, 0, z_pos), Point(x_min, 0, z_pos))

            for seg in self.segments:
                intersect, point = test_segment.intersect(seg)
                if intersect:
                    x_pos = point[0].X - resolution
                    while x_pos < (point[0].X + resolution):
                        iteration_position = Point(x_pos, 0, z_pos)
                        tool_shape = tool.get_shape_group(iteration_position)
                        if self.intersects_group(tool_shape) is False:
                            # tool.draw_shape(iteration_position)
                            points.append(iteration_position)
                            break
                        x_pos += resolution * 0.5
                    break

            z_pos -= resolution

        defeature_split = time.time()
        print('defeature elaspsed:', defeature_split - start)

        if len(points):
            seg_group = SegmentGroup()
            for idx, point in enumerate(points):
                if idx >= 1:
                    seg = Segment(points[idx-1], points[idx])
                    seg_group.add_segment(seg)

            seg_group.create_freecad_shape('paff')

            # attempt simplification
            sim_rdp_points = self.rdp(points, resolution)

            simplify_split = time.time()
            print('simplify elaspsed:', simplify_split - defeature_split)

            if len(sim_rdp_points):
                sim_seg_group = SegmentGroup()
                for idx, point in enumerate(sim_rdp_points):
                    if idx >= 1:
                        sim_seg = Segment(sim_rdp_points[idx-1], sim_rdp_points[idx])
                        sim_seg_group.add_segment(sim_seg)

                sim_seg_group.create_freecad_shape('sim_paff')

        return sim_seg_group

    def rdp(self, points, tolerance):
        """Reduce point set using Ramer–Douglas–Peucker algorithm"""
        tolerance = tolerance * tolerance

        length = len(points)
        markers = [0] * length

        first = 0
        last = length - 1

        first_stack = []
        last_stack = []

        new_points = []

        markers[first] = 1
        markers[last] = 1

        while last:
            max_sqdist = 0

            for i in range(first, last):
                sqdist = Segment(points[first], points[last]).distance_to_point(points[i])

                if sqdist > max_sqdist:
                    index = i
                    max_sqdist = sqdist

            if max_sqdist > tolerance:
                markers[index] = 1

                first_stack.append(first)
                last_stack.append(index)

                first_stack.append(index)
                last_stack.append(last)

            if len(first_stack) == 0:
                first = None
            else:
                first = first_stack.pop()

            if len(last_stack) == 0:
                last = None
            else:
                last = last_stack.pop()

        for i in range(length):
            if markers[i]:
                new_points.append(points[i])

        return new_points

    def validate(self):
        """validate the segment group"""
        # check first segment starts at X0
        # check if the last segment ends at x0

        count = self.count()

        if count == 0:
            raise ValueError("Input Geometry Invalid")

        # check the first segment starts at x = 0
        start_segment = self.segments[0]

        if start_segment.start.X != 0:
            new_start_point = Point(0, 0, start_segment.start.Z)
            # check if the points are the same within rounding errors
            if new_start_point.is_same(start_segment.start):
                start_segment.start = new_start_point
            else:
                new_start_seg = Segment(new_start_point, start_segment.start)
                self.insert_segment(new_start_seg, 0)
                if self.count() != count + 1:
                    raise ValueError("Segmentgroup Validation Failed")

        # check the last segment end at x = 0
        count = self.count()
        end_segment = self.segments[-1]

        if end_segment.end.X != 0:
            new_end_point = Point(0, 0, end_segment.end.Z)
            # check if the points are the same within rounding errors
            if new_end_point.is_same(end_segment.end):
                end_segment.end = new_end_point

    def create_freecad_shape(self, name):
        """ create a FreeCAD shape for debugging"""
        import FreeCAD
        import Part

        if self.count == 0:
            raise ValueError("Input Segment Group")

        part_edges = []
        for segment in self.segments:
            start_point = FreeCAD.Vector(segment.start.X, segment.start.Y, segment.start.Z)
            end_point = FreeCAD.Vector(segment.end.X, segment.end.Y, segment.end.Z)

            if segment.bulge == 0:
                edge = Part.makeLine(start_point, end_point)
            else:
                center = segment.get_centre_point()
                axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                start_angle = center.angle_to(segment.start) - 90
                end_angle = center.angle_to(segment.end) - 90
                if segment.bulge > 0:
                    edge = Part.makeCircle(segment.get_radius(),
                                           FreeCAD.Vector(center.X, center.Y, center.Z),
                                           axis, start_angle, end_angle)
                else:
                    edge = Part.makeCircle(segment.get_radius(),
                                           FreeCAD.Vector(center.X, center.Y, center.Z),
                                           axis, end_angle, start_angle)

            part_edges.append(edge)

        path_profile = Part.makeCompound(part_edges)
        Part.show(path_profile, name)
