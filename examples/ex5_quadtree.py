"""
LibLathe Example 5
This example creates a signed distance field
using a quadtree and plotting the quadtree nodes
"""

# Add LibLathe to the Python Path
import os
import sys

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.boundbox import BoundBox
from liblathe.base.quadtree import Quadtree
from liblathe.tool.tool import Tool
from liblathe.debug.debug import Debug

sg = SegmentGroup()
sg.addSegment(Segment(Point(0.0, -100.0) ,Point(27.5, -100.0), 0.000000))
sg.addSegment(Segment(Point(27.5, -100.0) ,Point(27.5, -85), 0.000000))
sg.addSegment(Segment(Point(27.5, -85) ,Point(14, -75), 0.000000))
sg.addSegment(Segment(Point(14, -75) ,Point(14, -15), 0.000000))
sg.addSegment(Segment(Point(14, -15) ,Point(0, 0), -0.3))
sg.addSegment(Segment(Point(0, 0) ,Point(10, 0), 0))

bb = sg.boundbox()
height = bb.XLength() + 10
width = bb.ZLength() + 10
size = max(height, width)
center = Point( size / 2, bb.ZMin + size / 2)

# Define a tool
tool = Tool()
tool.set_tool_from_string('DCMT070204R')
toolShape = tool.get_segmentgroup()

# Define stock bounds
stockPt1 = Point(0, -150)
stockPt2 = Point(50, 10)
StockBoundingBox = BoundBox(stockPt1, stockPt2)

defeatured = sg.defeature(StockBoundingBox, toolShape, False)
offset = defeatured.offset(0.5)

Debug().draw([sg, toolShape, defeatured, offset])

qt = Quadtree()
qt.initialise(defeatured, center, size, size)
offset = qt.getOffset(0.5)

nodes = qt.getNodes()
Debug().drawQuadtree(nodes, sg)
