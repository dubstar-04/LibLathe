from liblathe.gcode.command import Command
from liblathe.base.point import Point
from liblathe.base.segment import Segment


class Path:
    """Container Group for gcode path commands"""

    def __init__(self):
        self.commands = []

        cmd = Command('G18')  # xz plane
        self.commands.append(cmd)
    
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
                return pts[0].z
        return None

    def get_min_retract_x(self, segment, part_segment_group):
        """ returns the minimum x retract based on the current segments and the part_segments """

        part_segments = part_segment_group.get_segments()
        currentIdx = part_segments.index(segment)
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
    
    def previous_segment_connected(self, segments, segment):
        """returns bool if segment is connect to the previous segment"""

        currentIdx = segments.index(segment)
        previousIdx = currentIdx - 1

        if not currentIdx == 0:
            currentStartPt = segment.start
            previousEndPt = segments[previousIdx].end

            if currentStartPt.is_same(previousEndPt):
                return True

        return False

    def from_segment_group(self, operation, segment_group):
        """converts segmentgroup to gcode commands"""

        def get_pos(pnt):
            x = pnt.x
            z = pnt.z

            return Point(x, z)

        def get_arc_type(bulge):
            if bulge > 0:
                arcType = 'G3'
            else:
                arcType = 'G2'

            return arcType

        segments = segment_group.get_segments()

        for seg in segments:
            min_x_retract = segment_group.boundbox().x_max  # self.get_min_retract_x(seg, segment_group)
            x_retract = min_x_retract + operation.step_over * operation.finish_passes
            z_retract = segments[0].start.z

            # rapid to the start of the segmentgroup
            if segments.index(seg) == 0:
                pt = get_pos(seg.start)
                params = {'X': pt.x, 'Z': pt.z, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)

            # handle line segments
            if seg.bulge == 0:
                # handle unconnected segments
                if not self.previous_segment_connected(segments, seg) and segments.index(seg) != 0:
                    pt = get_pos(seg.start)
                    # rapid to the x_max
                    params = {'X': x_retract, 'F': operation.hfeed}
                    rapid = Command('G0', params)
                    self.commands.append(rapid)
                    # rapid at x_max to the start of the segment
                    params = {'X': x_retract, 'Z': pt.z, 'F': operation.hfeed}
                    rapid = Command('G0', params)
                    self.commands.append(rapid)
                    # rapid to the start of the start of the cutting move
                    params = {'X': pt.x, 'Z': pt.z, 'F': operation.hfeed}
                    cmd = Command('G0', params)
                    self.commands.append(cmd)
                
                # perform the cutting
                pt = get_pos(seg.end)
                params = {'X': pt.x, 'Z': pt.z, 'F': operation.hfeed}
                cmd = Command('G1', params)
                self.commands.append(cmd)
            # handle arc segments
            if seg.bulge != 0:
                pt1 = get_pos(seg.start)
                pt2 = get_pos(seg.end)
                # set the arc direction
                arcType = get_arc_type(seg.bulge)

                # set the arc parameters
                cen = get_pos(seg.get_centre_point()).sub(pt1)
                params = {'X': pt2.x, 'Z': pt2.z, 'I': cen.x, 'K': cen.z, 'F': operation.hfeed}
                cmd = Command(arcType, params)
                self.commands.append(cmd)

            # handle the lead out at the end of the segmentgroup
            if segments.index(seg) == len(segments) - 1:
                pt = get_pos(seg.end)
                # TODO: Remove the F parameter from rapid moves
                params = {'X': x_retract, 'Z': pt.z, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)

                params = {'X': x_retract, 'Z': z_retract, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)