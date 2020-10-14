import LibLathe.LLUtils as utils
from LibLathe.LLSegmentGroup import SegmentGroup
from LibLathe.LLTool import Tool


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.stock = None
        self.tool = Tool()
        self.part_segment_group = SegmentGroup()

        self.finishing_paths = []
        self.clearing_paths = []

        self.min_dia = 0
        self.extra_dia = 0
        self.start_offset = 0
        self.end_offset = 0
        self.allow_grooving = False
        self.allow_facing = False
        self.allow_roughing = True
        self.allow_finishing = True
        self.step_over = 1.5
        self.finish_passes = 2
        self.hfeed = 100
        self.vfeed = 50

    def set_params(self, params):
        """Set operations parameters"""

        for param in params:
            setattr(self, param, params[param])

    def get_params(self):
        """Return operations parameters"""
        pass

    def get_gcode(self):
        """Base function for all turning operations"""

        self.remove_the_groove()
        self.offset_part_outline()
        self.generate_path()
        Path = self.generate_gcode()
        return Path

    def remove_the_groove(self):
        """Remove grooves and undercuts from part geometry"""

        if not self.allow_grooving:
            self.part_segment_group = utils.remove_the_groove(self.part_segment_group, self.stock.ZMin, self.tool)

    def offset_part_outline(self):
        """Offsets the part to generate machining passes"""

        if self.allow_finishing:
            # If we are allowed finishing passes, add the part segment group to the finishing paths.
            self.finishing_paths.append(self.part_segment_group)
            f_pass = 1
            while f_pass != self.finish_passes:
                segmentGroup = utils.offsetPath(self.part_segment_group, self.step_over * f_pass)
                self.finishing_paths.append(segmentGroup)
                f_pass += 1

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
