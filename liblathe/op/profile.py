import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class ProfileOP(liblathe.op.base.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""
        # get the defeature part profile
        profile_segment_group = self.part_segment_group.defeature(self.stock.z_min, self.tool, self.allow_grooving)
        # define the base segment group using the stock to leave as a datum
        base_segment_group = profile_segment_group.offset_path(self.stock_to_leave)
        f_pass = 0
        while f_pass < self.finish_passes:
            # create a new segment group
            segmentgroup = SegmentGroup()
            # generate the offset profile path
            segmentgroup.extend(base_segment_group.offset_path(self.step_over * f_pass))
            # check if the generated pass intersects the part. use a small offset to reduce false positives
            if segmentgroup.intersects_group(self.part_segment_group.offset_path(-0.001)):
                raise ValueError("Calculated profile path intersects part")
            # add lead in to the profile path
            self.add_leadin(segmentgroup)
            # add the segment group to the tool paths
            self.tool_paths.append(segmentgroup)
            # increment f_pass to the next pass
            f_pass += 1

    def add_leadin(self, segmentgroup):
        # get the first segment of the segment group
        segment = segmentgroup.get_segments()[0]
        # calculate the new z_pos with lead in
        z_pos = segment.start.Z + self.clearance
        # create the new start point
        start_point = Point(segment.start.X, segment.start.Y, z_pos)
        # use the segments start as the leadin end point
        end_point = segment.start
        # create the leadin segment
        leadin = Segment(start_point, end_point)
        # add the leadin segment at the start of segment group
        segmentgroup.insert_segment(leadin, 0)

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = []

        for segmentgroup in reversed(self.tool_paths):
            finish = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
            path.extend(finish)

        return path
