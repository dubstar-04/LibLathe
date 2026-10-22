import os
import subprocess
import sys
import textwrap
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.quadtree import Node, Quadtree
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

    def coordinates(self, points):
        return [(point.X, point.Z) for point in points]

    def test_repeated_offsets_match_fresh_tree(self):
        for offset in (1, 3, 1):
            fresh = Quadtree()
            fresh.initialise(self.sg, Point(15, -5), 30, 30)
            expected = self.coordinates(fresh.getOffset(offset))
            self.assertEqual(self.coordinates(self.qt.getOffset(offset)), expected)
            self.assertEqual(len(self.qt.getNodes()), len(fresh.getNodes()))

    def test_reinitialised_tree_matches_fresh_tree(self):
        self.qt.getOffset(5)
        group = SegmentGroup()
        group.addSegment(Segment(Point(0, 0), Point(2, 0)))
        group.addSegment(Segment(Point(2, 0), Point(2, -4)))
        group.addSegment(Segment(Point(2, -4), Point(0, -4)))
        self.qt.initialise(group, Point(4, 0), 8, 8)
        fresh = Quadtree()
        fresh.initialise(group, Point(4, 0), 8, 8)
        expected = self.coordinates(fresh.getOffset(1))
        self.assertEqual(len(expected), 32)
        for _ in range(3):
            self.assertEqual(self.coordinates(self.qt.getOffset(1)), expected)
            self.assertEqual(len(self.qt.getNodes()), len(fresh.getNodes()))

    def test_initial_node_values(self):
        node = Node()
        self.assertEqual((node.center.X, node.center.Z), (0, 0))
        self.assertEqual((node.width, node.height, node.sdv), (0, 0, 0))
        root, = Quadtree().getNodes()
        self.assertEqual((root.center.X, root.center.Z), (0, 0))
        self.assertEqual((root.width, root.height, root.sdv), (0, 0, 0))
        root, = self.qt.getNodes()
        self.assertEqual((root.center.X, root.center.Z), (15, -5))
        self.assertEqual((root.width, root.height, root.sdv), (30, 30, 0))

    def test_source_geometry_lifetime(self):
        script = textwrap.dedent("""
            import gc
            import unittest
            import weakref

            from liblathe.base.point import Point
            from liblathe.base.quadtree import Quadtree
            from liblathe.base.segment import Segment
            from liblathe.base.segmentgroup import SegmentGroup

            check = unittest.TestCase()
            tree = Quadtree()
            references = []
            for width in (2, 3):
                group = SegmentGroup()
                group.addSegment(Segment(Point(0, 0), Point(width, 0)))
                group.addSegment(Segment(Point(width, 0), Point(width, -4)))
                group.addSegment(Segment(Point(width, -4), Point(0, -4)))
                references.append(weakref.ref(group))
                tree.initialise(group, Point(4, 0), 8, 8)
                expected = [(p.X, p.Z) for p in tree.getOffset(1)]
                check.assertTrue(expected)
                del group
                gc.collect()
                for reference in references:
                    check.assertIsNotNone(reference())
                check.assertEqual(
                    [(p.X, p.Z) for p in tree.getOffset(1)], expected
                )

            del tree
            gc.collect()
            for reference in references:
                check.assertIsNone(reference())
        """)
        result = subprocess.run(
            [sys.executable, '-c', script],
            cwd=parentFolder,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
