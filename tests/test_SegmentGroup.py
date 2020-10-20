import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(os.path.dirname(thisFolder))
sys.path.append(parentFolder)
from LibLathe.LLPoint import Point
from LibLathe.LLSegment import Segment
from LibLathe.LLSegmentGroup import SegmentGroup


class test_segment_group(unittest.TestCase):
    """Test for LLSegmentGroup.py"""
    def setUp(self):
        self.segmentGroup = SegmentGroup()
        self.segmentGroup2 = SegmentGroup()

        self.pt1 = Point(0, 0, 0)
        self.pt2 = Point(100, 0, 100)
        self.pt3 = Point(100, 0, 0)
        self.pt4 = Point(0, 0, 100)
        self.pt5 = Point(-120.12, 0, 214.09)
        self.pt6 = Point(-179.88, 0, 85.91)
        self.pt7 = Point(-214.09, 0, 179.88)
        self.pt8 = Point(-85.91, 0, 120.12)
        self.pt9 = Point(-164.74, 0, 118.39)
        self.pt10 = Point(-137.55, 0, 176.70)

        self.lineSegment1 = Segment(self.pt1, self.pt2)
        self.lineSegment2 = Segment(self.pt5, self.pt6)
        self.lineSegment3 = Segment(self.pt9, self.pt10)

        self.inverseLineSegment1 = Segment(self.pt3, self.pt4)

        self.hfeed = 100
        self.vfeed = 50
        self.step_over = 1.5

    def test_add_segment(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        segmentStart = self.segmentGroup.segments[0].start
        segmentEnd = self.segmentGroup.segments[0].end
        self.assertEqual(segmentStart, self.pt1)
        self.assertEqual(segmentEnd, self.pt2)

    def test_get_segments(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        segments = self.segmentGroup.get_segments()
        segmentStart = segments[0].start
        segmentEnd = segments[0].end
        self.assertEqual(segmentStart, self.pt1)
        self.assertEqual(segmentEnd, self.pt2)

        self.assertEqual(len(segments), 1)

    def test_extend(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        self.assertEqual(len(self.segmentGroup.segments), 1)

        self.segmentGroup2.add_segment(self.lineSegment2)
        self.segmentGroup.extend(self.segmentGroup2)
        self.assertEqual(len(self.segmentGroup.segments), 2)

    def test_count(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        count = self.segmentGroup.count()
        self.assertEqual(count, 1)

        self.segmentGroup.add_segment(self.lineSegment2)
        count = self.segmentGroup.count()
        self.assertEqual(count, 2)

    def test_boundbox(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        XMin = boundbox.XMin
        self.assertEqual(XMin, min(self.pt1.X, self.pt2.X))
        YMin = boundbox.YMin
        self.assertEqual(YMin, min(self.pt1.Y, self.pt2.Y))
        ZMin = boundbox.ZMin
        self.assertEqual(ZMin, min(self.pt1.Z, self.pt2.Z))
        XMax = boundbox.XMax
        self.assertEqual(XMax, max(self.pt1.X, self.pt2.X))
        YMax = boundbox.YMax
        self.assertEqual(YMax, max(self.pt1.Y, self.pt2.Y))
        ZMax = boundbox.ZMax
        self.assertEqual(ZMax, max(self.pt1.Z, self.pt2.Z))

    def test_join_segments(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        self.segmentGroup.join_segments()
        start = self.segmentGroup.segments[0].start
        end = self.segmentGroup.segments[0].end
        self.assertEqual(start, self.pt1)
        self.assertEqual(end, self.pt2)

    def test_previous_segment_connected_false(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        self.segmentGroup.add_segment(self.lineSegment2)
        self.assertFalse(self.segmentGroup.previous_segment_connected(self.lineSegment2))

    def test_previous_segment_connected_true(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        self.segmentGroup.add_segment(self.inverseLineSegment1)
        self.assertFalse(self.segmentGroup.previous_segment_connected(self.inverseLineSegment1))

    def test_get_min_retract_x(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment1, self.segmentGroup)
        self.assertEqual(min_x, 100)

        self.segmentGroup.add_segment(self.lineSegment3)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment3, self.segmentGroup)
        self.assertEqual(min_x,  -164.74)

    def test_to_commands_size(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.hfeed, self.vfeed)
        self.assertEqual(len(cmds), 7)

    def test_to_commands_movement(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.hfeed, self.vfeed)
        # Expected return
        # Command Movements
        # ['G18', 'G0', 'G0', 'G0', 'G1', 'G0', 'G0']
        self.assertEqual(cmds[0].Movement, 'G18')
        self.assertEqual(cmds[1].Movement, 'G0')
        self.assertEqual(cmds[2].Movement, 'G0')
        self.assertEqual(cmds[3].Movement, 'G0')
        self.assertEqual(cmds[4].Movement, 'G1')
        self.assertEqual(cmds[5].Movement, 'G0')
        self.assertEqual(cmds[6].Movement, 'G0')

    def test_to_commands_params(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.hfeed, self.vfeed)
        # Expected return
        # Command Params
        # {}
        # {'X': 0, 'Y': 0, 'Z': 101.5, 'F': 100}
        # {'X': 0, 'Y': 0, 'Z': 0, 'F': 100}
        # {'X': 0, 'Y': 0, 'Z': 0, 'F': 100}
        # {'X': 100, 'Y': 0, 'Z': 100, 'F': 100}
        # {'X': 98.5, 'Y': 0, 'Z': 100, 'F': 100}
        # {'X': 98.5, 'Y': 0, 'Z': 101.5, 'F': 100}
        self.assertEqual(cmds[0].Params, {})
        self.assertEqual(cmds[1].Params, {'X': 0, 'Y': 0, 'Z': 101.5, 'F': 100})
        self.assertEqual(cmds[2].Params, {'X': 0, 'Y': 0, 'Z': 0, 'F': 100})
        self.assertEqual(cmds[3].Params, {'X': 0, 'Y': 0, 'Z': 0, 'F': 100})
        self.assertEqual(cmds[4].Params, {'X': 100, 'Y': 0, 'Z': 100, 'F': 100})
        self.assertEqual(cmds[5].Params, {'X': 98.5, 'Y': 0, 'Z': 100, 'F': 100})
        self.assertEqual(cmds[6].Params, {'X': 98.5, 'Y': 0, 'Z': 101.5, 'F': 100})


if __name__ == '__main__':
    unittest.main()
