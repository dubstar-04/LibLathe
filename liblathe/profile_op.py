import liblathe.base_op


class ProfileOP(liblathe.base_op.BaseOP):

    def generate_path(self):
        """Generate the path for the profile operation"""

        profile_segment_group = self.part_segment_group.defeature(self.stock.z_min, self.tool, self.allow_grooving)
        base_segment_group = profile_segment_group.offset_path(self.stock_to_leave)
        self.tool_paths.append(base_segment_group)
        f_pass = 1
        while f_pass < self.finish_passes:
            segmentgroup = base_segment_group.offset_path(self.step_over * f_pass)
            
            if segmentgroup.intersects_group(self.part_segment_group):
                raise ValueError("Calculated profile path intersects part")
            
            self.tool_paths.append(segmentgroup)
            f_pass += 1

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        path = []

        for segmentgroup in reversed(self.tool_paths):
            finish = segmentgroup.to_commands(self.part_segment_group, self.stock, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
            path.extend(finish)

        return path
