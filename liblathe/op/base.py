from liblathe.base.segmentgroup import SegmentGroup
import math


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.stock = None
        self.tool = None
        self.partSegmentGroup = SegmentGroup()

        self.tool_paths = []

        self.allow_grooving = False
        self.step_over = 1.5
        self.finish_passes = 1
        self.stock_to_leave = 0
        self.hfeed = 100
        self.vfeed = 50
        self.clearance = 3

        self.leadin_angle = math.pi * 1.5
        self.leadout_angle = math.pi * 1.75

    def setParams(self, params):
        """Set operations parameters"""

        for param in params:
            if hasattr(self, param):
                setattr(self, param, params[param])
            else:
                raise Warning("Attempting to set undefined parameter '%s'" % param)

    def getParams(self):
        """Return operations parameters"""
        return {'allow_grooving': self.allow_grooving, 'step_over': self.step_over,
            'finish_passes': self.finish_passes, 'stock_to_leave': self.stock_to_leave, 'hfeed': self.hfeed,
            'vfeed': self.vfeed, 'clearance': self.clearance}

    def getGCode(self):
        """Base function for all turning operations"""

        if self.tool is None:
            raise Warning("Tool is unset")

        self.generatePath()
        path = self.generateGCode()
        return path

    def generatePath(self):
        """Main processing function for each op"""
        pass

    def generateGCode(self):
        """Generate Gcode for the op segments"""

        return ""

    def addPartSegments(self, partSegments):
        """Add edges to define the part geometry partSegments = array of LibLathe segments"""

        for segment in partSegments:
            self.partSegmentGroup.addSegment(segment)

        self.partSegmentGroup.validate()
        # self.partSegmentGroup.create_freecad_shape('partSegmentGroup')

    def add_stock(self, stockBoundbox):
        """Define bounding box for the stock material stockBoundbox = LibLathe BoundBox"""
        self.stock = stockBoundbox

    def add_tool(self, tool):
        """Set the tool for the operation"""
        self.tool = tool
