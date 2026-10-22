import os
import math
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

    def node_values(self, nodes):
        return [(n.center.X, n.center.Z, n.width, n.height, n.sdv) for n in nodes]

    def test_node_snapshots_preserve_preorder_and_values(self):
        rectangle = SegmentGroup()
        for start, end in (
            ((0, 0), (2, 0)), ((2, 0), (2, -4)), ((2, -4), (0, -4)),
        ):
            rectangle.addSegment(Segment(Point(*start), Point(*end)))
        arc = SegmentGroup()
        arc.addSegment(Segment(Point(0, 0), Point(2, -2), math.tan(math.pi / 8)))
        for group in (rectangle, arc):
            for offset in (0, 0.5):
                with self.subTest(group=group, offset=offset):
                    tree = Quadtree()
                    tree.initialise(group, Point(4, -2), 8, 8)
                    tree.getOffset(offset)
                    expected = []

                    def visit(x, z, width):
                        value = group.sdv(Point(x, z))
                        expected.append((x, z, width, width, value))
                        radius = width * math.sqrt(2) / 2
                        if width <= 0.05 or not value - radius <= offset <= value + radius:
                            return
                        for dx, dz in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
                            visit(x + dx * width / 4, z + dz * width / 4, width / 2)

                    visit(4, -2, 8)
                    self.assertEqual(self.node_values(tree.getNodes()), expected)

    def test_node_snapshots_are_independent_of_tree_state(self):
        self.qt.getOffset(1)
        nodes = self.qt.getNodes()
        expected = self.node_values(nodes)
        nodes[0].center.X = -999
        nodes[0].width = -1
        nodes[0].sdv = 123
        self.assertEqual(self.node_values(self.qt.getNodes()), expected)
        modified = self.node_values(nodes)
        self.qt.getOffset(3)
        self.assertEqual(self.node_values(nodes), modified)
        self.qt.initialise(self.sg, Point(16, -6), 32, 32)
        self.assertEqual(self.node_values(self.qt.getNodes()), [(16, -6, 32, 32, 0)])
        self.assertEqual(self.node_values(nodes), modified)

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
        self.assertGreater(len(expected), 1)
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

    def test_invalid_inputs_in_subprocess(self):
        script = textwrap.dedent("""
            import resource
            import unittest

            from liblathe.base.point import Point
            from liblathe.base.quadtree import Quadtree
            from liblathe.base.segment import Segment
            from liblathe.base.segmentgroup import SegmentGroup

            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            check = unittest.TestCase()
            tree = Quadtree()
            with check.assertRaisesRegex(RuntimeError, 'initialised'):
                tree.getOffset(1)

            group = SegmentGroup()
            group.addSegment(Segment(Point(0, 0), Point(2, 0)))
            group.addSegment(Segment(Point(2, 0), Point(2, -4)))
            group.addSegment(Segment(Point(2, -4), Point(0, -4)))
            empty = SegmentGroup()
            tree.initialise(empty, Point(4, 0), 8, 8)
            with check.assertRaisesRegex(ValueError, 'empty'):
                tree.getOffset(1)

            for value in (float('inf'), -float('inf'), float('nan'), 0, -1):
                for width, height in ((value, 8), (8, value), (value, value)):
                    with check.assertRaises(ValueError):
                        tree.initialise(group, Point(4, 0), width, height)
            for value in (float('inf'), -float('inf'), float('nan')):
                for centre in (Point(value, 0), Point(4, value)):
                    with check.assertRaises(ValueError):
                        tree.initialise(group, centre, 8, 8)
            with check.assertRaises(ValueError):
                tree.initialise(None, Point(4, 0), 8, 8)
            with check.assertRaises(ValueError):
                tree.initialise(group, Point(4, 0), 8, 4)

            tree.initialise(group, Point(4, 0), 8, 8)
            expected = [(p.X, p.Z) for p in tree.getOffset(1)]
            for value in (float('inf'), -float('inf'), float('nan')):
                with check.assertRaises(ValueError):
                    tree.getOffset(value)
                check.assertEqual([(p.X, p.Z) for p in tree.getOffset(1)], expected)
            check.assertEqual(tree.getOffset(100), [])
            check.assertEqual([(p.X, p.Z) for p in tree.getOffset(1)], expected)
        """)
        result = subprocess.run(
            [sys.executable, '-c', script],
            cwd=parentFolder,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejected_initialisation_preserves_valid_tree(self):
        expected = self.coordinates(self.qt.getOffset(1))
        replacement = SegmentGroup()
        replacement.addSegment(Segment(Point(0, 0), Point(1, -1)))
        for centre, width, height in (
            (Point(4, 0), 8, 4),
            (Point(float('nan'), 0), 8, 8),
            (Point(4, 0), 0, 0),
        ):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    self.qt.initialise(replacement, centre, width, height)
                self.assertEqual(self.coordinates(self.qt.getOffset(1)), expected)

    def test_zero_and_negative_offsets_remain_supported(self):
        for offset in (0, -0.1):
            with self.subTest(offset=offset):
                fresh = Quadtree()
                fresh.initialise(self.sg, Point(15, -5), 30, 30)
                expected = self.coordinates(fresh.getOffset(offset))
                self.assertTrue(expected)
                self.assertEqual(self.coordinates(self.qt.getOffset(offset)), expected)

    def test_start_point_is_refreshed_after_source_changes(self):
        group = SegmentGroup()
        group.addSegment(Segment(Point(10, 0), Point(10, -10)))
        tree = Quadtree()
        tree.initialise(group, Point(8, -4), 16, 16)
        self.assertLessEqual(max(p.Z for p in tree.getOffset(1)), 0)
        group.insertSegment(Segment(Point(0, 2), Point(10, 0)), 0)
        actual = tree.getOffset(1)
        self.assertGreater(max(p.Z for p in actual), 1)
        fresh = Quadtree()
        fresh.initialise(group, Point(8, -4), 16, 16)
        self.assertEqual(self.coordinates(actual), self.coordinates(fresh.getOffset(1)))


if __name__ == '__main__':
    unittest.main()
