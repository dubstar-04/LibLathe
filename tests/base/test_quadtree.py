import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.quadtree import Quadtree
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

#from liblathe.debug.debug import Debug

class test_quadtree(unittest.TestCase):
    """Test for quadtree.py"""
    def setUp(self):

        self.sg = SegmentGroup()
        self.sg.addSegment(Segment(Point(0.0, 0.0) ,Point(10, 0.0)))
        self.sg.addSegment(Segment(Point(10, 0.0) ,Point(10, -20)))
        self.sg.addSegment(Segment(Point(10, -20) ,Point(0, -20)))

        bb = self.sg.boundbox()
        height = bb.XLength() + 10
        width = bb.ZLength() + 10
        size = max(height, width)
        center = Point( size / 2, bb.ZMin + size / 2)

        self.qt = Quadtree()
        self.qt.initialise(self.sg, center, size, size)

    def test_getOffset(self):
        offsetPoints = self.qt.getOffset(5)
        self.assertGreater(len(offsetPoints),  0)
        self.assertAlmostEqual(offsetPoints[0].X, 15.0, 4)
        #self.assertAlmostEqual(offsetPoints[0].Z, 0.0, 4)
        self.assertAlmostEqual(offsetPoints[-1].X, 15.0, 4)

        #offsetSegmentGroup = SegmentGroup().fromPoints(offsetPoints)
        #Debug().draw([self.sg, offsetSegmentGroup])

    def test_getNodes(self):
        #run the offset
        self.qt.getOffset(5)
        nodes = self.qt.getNodes()
        print(len(nodes))
        self.assertGreater(len(nodes), 100)

    def test_insideNode(self):
        #TODO: how to test private methods?
        pass


if __name__ == '__main__':
    unittest.main()
