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


class test_segment_group(unittest.TestCase):
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

    def test_add_segment(self):
        self.segmentGroup.add_segment(self.lineSegment2)
        self.segmentGroup.insert_segment(self.lineSegment1, 0)
        segmentStart = self.segmentGroup.get_segments()[0].start
        segmentEnd = self.segmentGroup.get_segments()[0].end
        self.assertEqual(segmentStart.x, self.pt1.x)
        self.assertEqual(segmentStart.z, self.pt1.z)
        self.assertEqual(segmentEnd.x, self.pt2.x)
        self.assertEqual(segmentEnd.z, self.pt2.z)

    def test_insert_segment(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        segmentStart = self.segmentGroup.get_segments()[0].start
        segmentEnd = self.segmentGroup.get_segments()[0].end
        self.assertEqual(segmentStart.x, self.pt1.x)
        self.assertEqual(segmentStart.z, self.pt1.z)
        self.assertEqual(segmentEnd.x, self.pt2.x)
        self.assertEqual(segmentEnd.z, self.pt2.z)

    def test_get_segments(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        segments = self.segmentGroup.get_segments()
        segmentStart = segments[0].start
        segmentEnd = segments[0].end
        self.assertEqual(segmentStart.x, self.pt1.x)
        self.assertEqual(segmentStart.z, self.pt1.z)
        self.assertEqual(segmentEnd.x, self.pt2.x)
        self.assertEqual(segmentEnd.z, self.pt2.z)

        self.assertEqual(len(segments), 1)

    def test_extend(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        self.assertEqual(len(self.segmentGroup.get_segments()), 1)

        self.segmentGroup2.add_segment(self.lineSegment2)
        self.segmentGroup.extend(self.segmentGroup2)
        self.assertEqual(len(self.segmentGroup.get_segments()), 2)

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
        x_min = boundbox.x_min
        self.assertEqual(x_min, min(self.pt1.x, self.pt2.x))
        z_min = boundbox.z_min
        self.assertEqual(z_min, min(self.pt1.z, self.pt2.z))
        x_max = boundbox.x_max
        self.assertEqual(x_max, max(self.pt1.x, self.pt2.x))
        z_max = boundbox.z_max
        self.assertEqual(z_max, max(self.pt1.z, self.pt2.z))

    '''
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
        self.segmentGroup.add_segment(self.lineSegment4)
        self.assertTrue(self.segmentGroup.previous_segment_connected(self.lineSegment4))

    def test_get_min_retract_x(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment1, self.segmentGroup)
        self.assertEqual(min_x, 100)

        self.segmentGroup.add_segment(self.lineSegment3)
        min_x = self.segmentGroup.get_min_retract_x(self.lineSegment3, self.segmentGroup)
        self.assertEqual(min_x, -164.74)

    def test_to_commands_size(self):
        self.segmentGroup.add_segment(self.lineSegment1)
        boundbox = self.segmentGroup.boundbox()
        cmds = self.segmentGroup.to_commands(self.segmentGroup, boundbox, self.step_over, self.finish_passes, self.hfeed, self.vfeed)
        self.assertEqual(len(cmds), 5)

    def test_to_commands_movement(self):
        self.segmentGroup.add_segment(self.lineSegment1)
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
        self.segmentGroup.add_segment(self.lineSegment1)
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
        tool.add_segment(Segment(tool_point_1, tool_point_2))
        tool.add_segment(Segment(tool_point_2, tool_point_3))
        tool.add_segment(Segment(tool_point_3, tool_point_4))
        tool.add_segment(Segment(tool_point_4, tool_point_1))

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

        sg.add_segment(Segment(Pt1, Pt2, 0.7739018038161916))
        sg.add_segment(Segment(Pt2, Pt3))
        sg.add_segment(Segment(Pt3, Pt4))
        sg.add_segment(Segment(Pt4, Pt5, -0.7543428437659994))
        sg.add_segment(Segment(Pt5, Pt7))
        sg.add_segment(Segment(Pt7, Pt8))
        sg.add_segment(Segment(Pt8, Pt9))
        sg.add_segment(Segment(Pt9, Pt10))

        part_boundbox = sg.boundbox()
        stock_min = Point(part_boundbox.x_min, part_boundbox.z_min - 5)
        stock_max = Point(part_boundbox.x_max + 5, part_boundbox.z_max + 5)
        stock = BoundBox(stock_min, stock_max)

        defeatured_group = sg.defeature(stock, tool, False)

        self.assertTrue(defeatured_group.count() > 0)

    def test_from_points(self):
        points = [Point(100, 100), Point(0, 0), Point(100, -100)]
        sg = SegmentGroup().from_points(points)
        segs = sg.get_segments()
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0].start.x, 100)
        self.assertEqual(segs[0].start.z, 100)
        self.assertEqual(segs[0].end.x, 0)
        self.assertEqual(segs[0].end.z, 0)

    def test_get_rdp(self):
        points = [Point(100, 100), Point(30, 30), Point(31, 31), Point(0, 0), Point(10, 10), Point(15, 15), Point(100, -100)]
        points_out = SegmentGroup().get_rdp(points, 0.1)
        self.assertTrue(len(points_out) < len(points))

    def test_sdv(self):
        PartPt1 = Point(0, 0)
        PartPt2 = Point(15, -5)
        PartPt3 = Point(15, -15)
        PartPt4 = Point(0, -20)

        sg = SegmentGroup()

        sg.add_segment(Segment(PartPt1, PartPt2))
        sg.add_segment(Segment(PartPt2, PartPt3))
        sg.add_segment(Segment(PartPt3, PartPt4))

        self.assertEqual(sg.sdv(Point(0, 10)), 10)
        self.assertEqual(sg.sdv(Point(10, -10)), -5)
        self.assertEqual(sg.sdv(Point(20, -10)), 5)

    def test_isInside(self):
        PartPt1 = Point(0, 0)
        PartPt2 = Point(15, -5)
        PartPt3 = Point(15, -15)
        PartPt4 = Point(0, -20)

        sg = SegmentGroup()

        sg.add_segment(Segment(PartPt1, PartPt2))
        sg.add_segment(Segment(PartPt2, PartPt3))
        sg.add_segment(Segment(PartPt3, PartPt4))

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
