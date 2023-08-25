import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

from liblathe.gcode.path import Path
from liblathe.debug.debug import Debug


class ProfileOP(liblathe.op.base.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""
        # get the defeature part profile
        profile_segment_group = self.part_segment_group.defeature(self.stock, self.tool.get_shape_group(), self.allow_grooving)
        # define the base segment group using the stock to leave as a datum
        base_segment_group = profile_segment_group.offset(self.stock_to_leave)
        # add lead in to the profile path
        self.add_leadin(base_segment_group)
        f_pass = 0
        while f_pass < self.finish_passes:
            # create a new segment group
            segmentgroup = SegmentGroup()
            # generate the offset profile path
            segmentgroup.extend(base_segment_group.offset(self.step_over * f_pass))

            # check if the generated pass intersects the part. use a small offset to reduce false positives
            internal_offset = profile_segment_group.offset(-0.1)
            if segmentgroup.intersects_group(internal_offset):
                #Debug().draw([internal_offset, segmentgroup])
                raise ValueError("Calculated profile path intersects part")
            
            # add the segment group to the tool paths
            self.tool_paths.append(segmentgroup)
            # increment f_pass to the next pass
            f_pass += 1

    def add_leadin(self, segmentgroup):
        # get the first segment of the segment group
        segment = segmentgroup.get_segments()[0]
        #TODO: handle leadin when profiling a mid portion of a part
        # calculate the new z_pos with lead in
        if (segment.start.z < self.stock.z_max):
            z_pos = self.stock.z_max
        else:
            z_pos = segment.start.z + self.clearance
        # create the new start point
        start_point = Point(segment.start.x, z_pos)
        # use the segments start as the leadin end point
        end_point = segment.start
        # create the leadin segment
        leadin = Segment(start_point, end_point)
        # add the leadin segment at the start of segment group
        segmentgroup.insert_segment(leadin, 0)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = Path()

        for segmentgroup in reversed(self.tool_paths):
            path.from_segment_group(self, segmentgroup)

        return path.commands
