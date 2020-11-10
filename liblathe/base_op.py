from liblathe.segmentgroup import SegmentGroup


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.stock = None
        self.tool = None
        self.part_segment_group = SegmentGroup()

        self.tool_paths = []

        self.min_dia = 0
        self.extra_dia = 0
        self.start_offset = 0
        self.end_offset = 0
        self.allow_grooving = False
        self.step_over = 1.5
        self.finish_passes = 2
        self.stock_to_leave = 0
        self.hfeed = 100
        self.vfeed = 50

    def set_params(self, params):
        """Set operations parameters"""

        for param in params:
            setattr(self, param, params[param])

    def get_params(self):
        """Return operations parameters"""
        return {'min_dia': self.min_dia, 'extra_dia': self.extra_dia, 'start_offset': self.start_offset,
                'end_offset': self.end_offset, 'allow_grooving': self.allow_grooving, 'step_over': self.step_over,
                'finish_passes': self.finish_passes, 'stock_to_leave': self.stock_to_leave, 'hfeed': self.hfeed, 'vfeed': self.vfeed}

    def get_gcode(self):
        """Base function for all turning operations"""

        if self.tool is None:
            raise Warning("Tool is unset")

        self.generate_path()
        Path = self.generate_gcode()
        return Path

    def generate_path(self):
        """Main processing function for each op"""

        pass

    def generate_gcode(self):
        """Generate Gcode for the op segments"""

        return ""

    def add_part_edges(self, part_edges):
        """Add edges to define the part geometry part_edges = array of LibLathe segments"""

        for segment in part_edges:
            self.part_segment_group.add_segment(segment)

    def add_stock(self, stock_bb):
        """Define bounding box for the stock material stock_bb = LibLathe BoundBox"""
        self.stock = stock_bb

    def add_tool(self, tool):
        """Set the tool for the operation"""
        self.tool = tool
