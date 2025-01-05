import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
baseFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(baseFolder)
sys.path.append(parentFolder)

from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.boundbox import BoundBox


class test_segmentGroup(unittest.TestCase):
    """Test for segmentgroup.py"""
    def setUp(self):
        self.segmentGroup = SegmentGroup()
        self.segmentGroup2 = SegmentGroup()

        self.pt1 = Point(0, 0)
        self.pt2 = Point(100, 100)
        self.pt3 = Point(100, 0)
        self.pt4 = Point(0, 100)
        self.pt5 = Point(-120.12, 214.09)
        self.pt6 = Point(-179.88, 85.91)
        self.pt7 = Point(-214.09, 179.88)
        self.pt8 = Point(-85.91, 120.12)
        self.pt9 = Point(-164.74, 118.39)
        self.pt10 = Point(-137.55, 176.70)

        self.lineSegment1 = Segment(self.pt1, self.pt2)
        self.lineSegment2 = Segment(self.pt5, self.pt6)
        self.lineSegment3 = Segment(self.pt9, self.pt10)
        self.lineSegment4 = Segment(self.pt2, self.pt1)

        self.inverseLineSegment1 = Segment(self.pt3, self.pt4)

        self.hfeed = 100
        self.vfeed = 50
        self.step_over = 1.5
        self.finish_passes = 2

    def test_addSegment(self):
        self.segmentGroup.addSegment(self.lineSegment2)
        self.segmentGroup.insertSegment(self.lineSegment1, 0)
        segmentStart = self.segmentGroup.getSegments()[0].start
        segmentEnd = self.segmentGroup.getSegments()[0].end
        self.assertEqual(segmentStart.X, self.pt1.X)
        self.assertEqual(segmentStart.Z, self.pt1.Z)
        self.assertEqual(segmentEnd.X, self.pt2.X)
        self.assertEqual(segmentEnd.Z, self.pt2.Z)

    def test_insertSegment(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        segmentStart = self.segmentGroup.getSegments()[0].start
        segmentEnd = self.segmentGroup.getSegments()[0].end
        self.assertEqual(segmentStart.X, self.pt1.X)
        self.assertEqual(segmentStart.Z, self.pt1.Z)
        self.assertEqual(segmentEnd.X, self.pt2.X)
        self.assertEqual(segmentEnd.Z, self.pt2.Z)

    def test_getSegments(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        segments = self.segmentGroup.getSegments()
        segmentStart = segments[0].start
        segmentEnd = segments[0].end
        self.assertEqual(segmentStart.X, self.pt1.X)
        self.assertEqual(segmentStart.Z, self.pt1.Z)
        self.assertEqual(segmentEnd.X, self.pt2.X)
        self.assertEqual(segmentEnd.Z, self.pt2.Z)

        self.assertEqual(len(segments), 1)

    def test_extend(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        self.assertEqual(len(self.segmentGroup.getSegments()), 1)

        self.segmentGroup2.addSegment(self.lineSegment2)
        self.segmentGroup.extend(self.segmentGroup2)
        self.assertEqual(len(self.segmentGroup.getSegments()), 2)

    def test_count(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        count = self.segmentGroup.count()
        self.assertEqual(count, 1)

        self.segmentGroup.addSegment(self.lineSegment2)
        count = self.segmentGroup.count()
        self.assertEqual(count, 2)

    def test_boundbox(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        XMin = boundbox.XMin
        self.assertEqual(XMin, min(self.pt1.X, self.pt2.X))
        ZMin = boundbox.ZMin
        self.assertEqual(ZMin, min(self.pt1.Z, self.pt2.Z))
        XMax = boundbox.XMax
        self.assertEqual(XMax, max(self.pt1.X, self.pt2.X))
        ZMax = boundbox.ZMax
        self.assertEqual(ZMax, max(self.pt1.Z, self.pt2.Z))

    '''
    def test_join_segments(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        self.segmentGroup.join_segments()
        start = self.segmentGroup.segments[0].start
        end = self.segmentGroup.segments[0].end
        self.assertEqual(start, self.pt1)
        self.assertEqual(end, self.pt2)

    def test_previous_segment_connected_false(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        self.segmentGroup.addSegment(self.lineSegment2)
        self.assertFalse(self.segmentGroup.previous_segment_connected(self.lineSegment2))

    def test_previous_segment_connected_true(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        self.segmentGroup.addSegment(self.lineSegment4)
        self.assertTrue(self.segmentGroup.previous_segment_connected(self.lineSegment4))

    def test_get_min_retract_x(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment1, self.segmentGroup)
        self.assertEqual(min_x, 100)

        self.segmentGroup.addSegment(self.lineSegment3)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment3, self.segmentGroup)
        self.assertEqual(min_x, -164.74)

    def test_to_commands_size(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
        self.assertEqual(len(cmds), 5)

    def test_to_commands_movement(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
        # Expected return
        # Command movements
        # ['G18', 'G0', 'G0', 'G0', 'G1', 'G0', 'G0']
        self.assertEqual(cmds[0].movement, 'G18')
        self.assertEqual(cmds[1].movement, 'G0')
        self.assertEqual(cmds[2].movement, 'G1')
        self.assertEqual(cmds[3].movement, 'G0')
        self.assertEqual(cmds[4].movement, 'G0')

    def test_to_commands_params(self):
        #TODO: Validate
        self.segmentGroup.addSegment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.finish_passes, self.hfeed, self.vfeed)

        self.assertEqual(cmds[0].params, {})
        self.assertEqual(cmds[1].params, {'X': 0, 'Z': 0, 'F': 100})
        self.assertEqual(cmds[2].params, {'X': -100, 'Z': 100, 'F': 100})
        self.assertEqual(cmds[3].params, {'X': -97.0, 'Z': 100, 'F': 100})
        self.assertEqual(cmds[4].params, {'X': -97.0, 'Z': 0, 'F': 100})
    '''

    def test_defeature(self):

        # define tool shape
        tool_point_1 = Point(0, 0)
        tool_point_2 = Point(0, 5)
        tool_point_3 = Point(5, 5)
        tool_point_4 = Point(5, 0)

        tool = SegmentGroup()
        tool.addSegment(Segment(tool_point_1, tool_point_2))
        tool.addSegment(Segment(tool_point_2, tool_point_3))
        tool.addSegment(Segment(tool_point_3, tool_point_4))
        tool.addSegment(Segment(tool_point_4, tool_point_1))

        Pt1 = Point(0, 10)
        Pt2 = Point(4.85643, -8.74157)
        Pt3 = Point(9.5, -15.85)
        Pt4 = Point(5.4, -22)
        Pt5 = Point(5.4, -30)
        Pt7 = Point(5.4, -40)
        Pt8 = Point(13, -45)
        Pt9 = Point(13, -48)
        Pt10 = Point(0, -48)

        sg = SegmentGroup()

        sg.addSegment(Segment(Pt1, Pt2, 0.7739018038161916))
        sg.addSegment(Segment(Pt2, Pt3))
        sg.addSegment(Segment(Pt3, Pt4))
        sg.addSegment(Segment(Pt4, Pt5, -0.7543428437659994))
        sg.addSegment(Segment(Pt5, Pt7))
        sg.addSegment(Segment(Pt7, Pt8))
        sg.addSegment(Segment(Pt8, Pt9))
        sg.addSegment(Segment(Pt9, Pt10))

        part_boundbox = sg.boundbox()
        stock_min = Point(part_boundbox.XMin, part_boundbox.ZMin - 5)
        stock_max = Point(part_boundbox.XMax + 5, part_boundbox.ZMax + 5)
        stock = BoundBox(stock_min, stock_max)

        defeatured_group = sg.defeature(stock, tool, False)

        self.assertTrue(defeatured_group.count() > 0)

    def test_fromPoints(self):
        points = [Point(100, 100), Point(0, 0), Point(100, -100)]
        sg = SegmentGroup().fromPoints(points)
        segs = sg.getSegments()
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0].start.X, 100)
        self.assertEqual(segs[0].start.Z, 100)
        self.assertEqual(segs[0].end.X, 0)
        self.assertEqual(segs[0].end.Z, 0)

    def test_reduce(self):
        points = [Point(100, 100), Point(30, 30), Point(31, 31), Point(0, 0), Point(10, 10), Point(15, 15), Point(100, -100)]
        points_out = SegmentGroup().reduce(points, 0.1)
        self.assertTrue(len(points_out) < len(points))

    def test_sdv(self):
        PartPt1 = Point(0, 0)
        PartPt2 = Point(15, -5)
        PartPt3 = Point(15, -15)
        PartPt4 = Point(0, -20)

        sg = SegmentGroup()

        sg.addSegment(Segment(PartPt1, PartPt2))
        sg.addSegment(Segment(PartPt2, PartPt3))
        sg.addSegment(Segment(PartPt3, PartPt4))

        self.assertEqual(sg.sdv(Point(0, 10)), 10)
        self.assertEqual(sg.sdv(Point(10, -10)), -5)
        self.assertEqual(sg.sdv(Point(20, -10)), 5)

    def test_isInside(self):
        PartPt1 = Point(0, 0)
        PartPt2 = Point(15, -5)
        PartPt3 = Point(15, -15)
        PartPt4 = Point(0, -20)

        sg = SegmentGroup()

        sg.addSegment(Segment(PartPt1, PartPt2))
        sg.addSegment(Segment(PartPt2, PartPt3))
        sg.addSegment(Segment(PartPt3, PartPt4))

        # inside
        self.assertTrue(sg.isInside(Point(0, -1)))
        self.assertTrue(sg.isInside(Point(10, -10)))
        self.assertTrue(sg.isInside(Point(0, -19)))

        # on the boundary
        self.assertTrue(sg.isInside(Point(15, -10)))

        # outside
        self.assertFalse(sg.isInside(Point(0, 10)))
        self.assertFalse(sg.isInside(Point(10, 10)))
        self.assertFalse(sg.isInside(Point(16, -10)))
        self.assertFalse(sg.isInside(Point(10, -30)))



if __name__ == '__main__':
    unittest.main()
