from copy import copy

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.gcode.command import Command
from liblathe.tool.tool import ToolSide
import math


def reflect_x_segments(segments):
    return [Segment(Point(-segment.start.X, segment.start.Z),
                    Point(-segment.end.X, segment.end.Z), -segment.bulge)
            for segment in segments]


class BaseOP:
    """Base class for all turning operations."""

    def __init__(self):

        self.stock = None
        self.tool = None
        self.partSegmentGroup = SegmentGroup()

        self.tool_paths = []
        self.clearing_paths = []

        self.allow_grooving = False
        self.pass_offset = 1.5
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
        return {'allow_grooving': self.allow_grooving, 'pass_offset': self.pass_offset,
                'finish_passes': self.finish_passes, 'stock_to_leave': self.stock_to_leave, 'hfeed': self.hfeed,
                'vfeed': self.vfeed, 'clearance': self.clearance}

    def getGCode(self):
        """Base function for all turning operations"""

        if self.tool is None:
            raise Warning("Tool is unset")

        if self.tool.side == ToolSide.FAR:
            self.tool_paths = []
            self.clearing_paths = []
            if self.stock is None or self.stock.XMax > 1e-4 or self.stock.XMin >= 0:
                raise ValueError("Far-side stock must use negative X coordinates")
            if self.partSegmentGroup.boundbox().XMax > 1e-4:
                raise ValueError("Far-side part geometry must use negative X coordinates")
            planning = copy(self)
            planning.tool_paths = []
            planning.clearing_paths = []
            planning.stock = BoundBox(Point(-self.stock.XMax, self.stock.ZMin),
                                      Point(-self.stock.XMin, self.stock.ZMax))
            planning.partSegmentGroup = SegmentGroup()
            for segment in reflect_x_segments(self.partSegmentGroup.getSegments()):
                planning.partSegmentGroup.addSegment(segment)
            planning.tool = copy(self.tool)
            planning.tool.segmentGroup = SegmentGroup()
            for segment in reflect_x_segments(self.tool.get_segmentgroup().getSegments()):
                planning.tool.segmentGroup.addSegment(segment)
            planning.tool.tool_rotation = 0
            planning.tool.side = ToolSide.NEAR
            planning.generatePath()
            commands = planning.generateGCode()
            result = []
            for command in commands:
                parameters = dict(command.getParams())
                for name in ("X", "I"):
                    if name in parameters:
                        parameters[name] = -parameters[name]
                movement = {"G2": "G3", "G3": "G2", "G02": "G03", "G03": "G02"}.get(
                    command.get_movement(), command.get_movement())
                result.append(Command(movement, parameters))
            for name in ("tool_paths", "clearing_paths"):
                physical_paths = getattr(self, name)
                for group in getattr(planning, name):
                    physical = SegmentGroup()
                    for segment in reflect_x_segments(group.getSegments()):
                        physical.addSegment(segment)
                    physical_paths.append(physical)
            return result

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

    def add_stock_from_limits(self, xmin, xmax, zmin, zmax):
        """Define bounding box for the stock material xmin, xmax, zmin, zmax = float values defining the stock limits"""
        stockBoundbox = BoundBox(Point(xmin, zmin), Point(xmax, zmax))
        self.stock = stockBoundbox

    def add_tool(self, tool):
        """Set the tool for the operation"""
        self.tool = tool
