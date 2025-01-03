from liblathe.gcode.command import Command
from liblathe.base.point import Point
from liblathe.base.segment import Segment


class Path:
    """Container Group for gcode path commands"""

    def __init__(self):
        self.commands = []

        cmd = Command('G18')  # xz plane
        self.commands.append(cmd)

    def get_min_retract_x(self, segment, pass_segments, operation):
        """ returns the minimum x retract based on the current segments and the part_segments """

        # part_segments = partSegmentGroup.getSegments()
        currentIdx = pass_segments.index(segment)
        x_values = []

        # get the XMax from the current pass segments
        for idx, seg in enumerate(pass_segments):
            x_values.extend([seg.Boundbox().XMin, seg.Boundbox().XMax])
            if idx == currentIdx:
                break

        # get the XMax from the part segments up to the z position of the current segment
        seg_ZMax = segment.Boundbox().ZMax
        for part_seg in operation.partSegmentGroup.getSegments():

            part_seg_ZMax = part_seg.Boundbox().ZMax
            x_values.extend([part_seg.Boundbox().XMin, part_seg.Boundbox().XMax])

            if part_seg_ZMax < seg_ZMax:
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

            if currentStartPt.isSame(previousEndPt):
                return True

        return False

    def from_segment_group(self, operation, segment_group):
        """converts segmentgroup to gcode commands"""

        def get_pos(pnt):
            x = pnt.X
            z = pnt.Z

            return Point(x, z)

        def get_arc_type(bulge):
            if bulge > 0:
                arcType = 'G3'
            else:
                arcType = 'G2'

            return arcType

        segments = segment_group.getSegments()

        for seg in segments:
            min_x_retract = self.get_min_retract_x(seg, segments, operation)
            x_retract = min_x_retract + operation.step_over * operation.finish_passes
            z_retract = segments[0].start.Z

            # rapid to the start of the segmentgroup
            if segments.index(seg) == 0:
                pt = get_pos(seg.start)
                params = {'X': pt.X, 'Z': pt.Z, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)

            # handle line segments
            if seg.bulge == 0:
                # handle unconnected segments
                if not self.previous_segment_connected(segments, seg) and segments.index(seg) != 0:
                    pt = get_pos(seg.start)
                    # rapid to the XMax
                    params = {'X': x_retract, 'F': operation.hfeed}
                    rapid = Command('G0', params)
                    self.commands.append(rapid)
                    # rapid at XMax to the start of the segment
                    params = {'X': x_retract, 'Z': pt.Z, 'F': operation.hfeed}
                    rapid = Command('G0', params)
                    self.commands.append(rapid)
                    # rapid to the start of the start of the cutting move
                    params = {'X': pt.X, 'Z': pt.Z, 'F': operation.hfeed}
                    cmd = Command('G0', params)
                    self.commands.append(cmd)

                # perform the cutting
                pt = get_pos(seg.end)
                params = {'X': pt.X, 'Z': pt.Z, 'F': operation.hfeed}
                cmd = Command('G1', params)
                self.commands.append(cmd)
            # handle arc segments
            if seg.bulge != 0:
                pt1 = get_pos(seg.start)
                pt2 = get_pos(seg.end)
                # set the arc direction
                arcType = get_arc_type(seg.bulge)

                # set the arc parameters
                cen = get_pos(seg.getCentrePoint()).sub(pt1)
                params = {'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': operation.hfeed}
                cmd = Command(arcType, params)
                self.commands.append(cmd)

            # handle the lead out at the end of the segmentgroup
            if segments.index(seg) == len(segments) - 1:
                pt = get_pos(seg.end)
                # TODO: Remove the F parameter from rapid moves
                params = {'X': x_retract, 'Z': pt.Z, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)

                params = {'X': x_retract, 'Z': z_retract, 'F': operation.hfeed}
                rapid = Command('G0', params)
                self.commands.append(rapid)