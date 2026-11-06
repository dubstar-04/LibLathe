import unittest

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

    def test_offset_rejects_empty_and_nonfinite_inputs(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            self.segmentGroup.offset(1)
        self.segmentGroup.addSegment(Segment(Point(0, 0), Point(2, 0)))
        self.segmentGroup.addSegment(Segment(Point(2, 0), Point(2, -4)))
        self.segmentGroup.addSegment(Segment(Point(2, -4), Point(0, -4)))
        for offset in (float('inf'), -float('inf'), float('nan')):
            with self.subTest(offset=offset):
                with self.assertRaisesRegex(ValueError, 'finite'):
                    self.segmentGroup.offset(offset)

    def test_offset_reports_no_contour_and_recovers(self):
        self.segmentGroup.addSegment(Segment(Point(0, 0), Point(2, 0)))
        self.segmentGroup.addSegment(Segment(Point(2, 0), Point(2, -4)))
        self.segmentGroup.addSegment(Segment(Point(2, -4), Point(0, -4)))
        expected = self.segmentGroup.offset(-0.1)
        with self.assertRaisesRegex(RuntimeError, 'Offset produced no points'):
            self.segmentGroup.offset(-100)
        actual = self.segmentGroup.offset(-0.1)
        self.assertEqual(actual.count(), expected.count())
        for segment, reference in zip(actual.getSegments(), expected.getSegments()):
            self.assertEqual(
                (segment.start.X, segment.start.Z, segment.end.X, segment.end.Z),
                (reference.start.X, reference.start.Z, reference.end.X, reference.end.Z),
            )

    def test_offset_reports_single_point_contour(self):
        # Eroding a closed square by its inradius leaves one point.
        self.segmentGroup.addSegment(Segment(Point(0, 0), Point(2, 0)))
        self.segmentGroup.addSegment(Segment(Point(2, 0), Point(2, -2)))
        self.segmentGroup.addSegment(Segment(Point(2, -2), Point(0, -2)))
        self.segmentGroup.addSegment(Segment(Point(0, -2), Point(0, 0)))
        with self.assertRaisesRegex(RuntimeError, 'Offset produced fewer than two points'):
            self.segmentGroup.offset(-1)

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

    def test_getSegments_returns_independent_copies(self):
        self.segmentGroup.addSegment(self.lineSegment1)
        expected = self.segmentGroup.getSegments()[0].start.Z
        segments = self.segmentGroup.getSegments()
        segments[0].start.Z = expected + 100
        segments.clear()
        self.assertEqual(self.segmentGroup.count(), 1)
        self.assertEqual(self.segmentGroup.getSegments()[0].start.Z, expected)

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
        for move in defeatured_group.getSegments():
            for step in range(41):
                fraction = step / 40
                radial = move.start.X + (move.end.X - move.start.X) * fraction
                axial = move.start.Z + (move.end.Z - move.start.Z) * fraction
                for edge in tool.getSegments():
                    for sample in range(11):
                        along = sample / 10
                        point = Point(radial + edge.start.X + (edge.end.X - edge.start.X) * along,
                                      axial + edge.start.Z + (edge.end.Z - edge.start.Z) * along)
                        self.assertGreater(sg.sdv(point), 0)

    def test_defeature_preserves_scan_grid_at_thin_shoulders(self):
        part_vertices = [(0, 0), (1.003, 0), (1.003, -0.061), (1.007, -0.061),
                         (1.007, -0.064), (1.003, -0.064), (1.003, -0.2), (0, -0.2)]
        tool_vertices = [(0, 0), (0, 0.005), (0.004, 0.005), (0.004, 0), (0, 0)]
        references = {
            0: (0.017500000074505806, 0.007500000298023224, -0.20250001549720764,
                1.00749933719635, 1.0124993324279785),
            128: (128.01748657226562, 128.0074920654297, 127.79744720458984,
                  129.00848388671875, 129.01348876953125),
        }
        for shift, (start_z, corner_z, end_z, inner_x, outer_x) in references.items():
            for grooving in (False, True):
                with self.subTest(shift=shift, grooving=grooving):
                    part = SegmentGroup()
                    tool = SegmentGroup()
                    for start, end in zip(part_vertices, part_vertices[1:]):
                        part.addSegment(Segment(Point(*start), Point(*end)))
                    for start, end in zip(tool_vertices, tool_vertices[1:]):
                        tool.addSegment(Segment(Point(start[0] - shift, start[1] - shift),
                                                Point(end[0] - shift, end[1] - shift)))
                    contour = part.defeature(BoundBox(Point(0, -0.21), Point(3, 0.02)), tool, grooving)
                    segments = contour.getSegments()
                    self.assertEqual(
                        [(edge.start.X, edge.start.Z, edge.end.X, edge.end.Z, edge.bulge)
                         for edge in segments],
                        [(shift, start_z, inner_x, corner_z, 0),
                         (inner_x, corner_z, inner_x if grooving else outer_x, end_z, 0)],
                    )
                    for edge in segments:
                        part.validateToolSweep(tool, edge.start, edge.end)

    def test_defeature_keeps_first_clear_region_between_radial_walls(self):
        part = SegmentGroup()
        tool = SegmentGroup()
        for group, vertices in (
                (part, [(0, 0), (2, 0), (2, -0.16), (2.014, -0.16),
                        (2.014, 0), (2.018, 0), (2.018, -0.2), (0, -0.2)]),
                (tool, [(0, 0), (0, 0.005), (0.004, 0.005), (0.004, 0), (0, 0)])):
            for start, end in zip(vertices, vertices[1:]):
                group.addSegment(Segment(Point(*start), Point(*end)))
        for radial in (1, 2.015):
            with self.subTest(colliding_radial=radial):
                with self.assertRaises(RuntimeError):
                    part.validateToolSweep(tool, Point(radial, -0.05), Point(radial, -0.05))
        for radial in (2.0075, 2.025):
            with self.subTest(clear_radial=radial):
                part.validateToolSweep(tool, Point(radial, -0.05), Point(radial, -0.05))
        for grooving in (False, True):
            with self.subTest(grooving=grooving):
                contour = part.defeature(BoundBox(Point(0, -0.12), Point(3, 0.02)), tool, grooving)
                segments = contour.getSegments()
                self.assertTrue(any(2 < edge.end.X < 2.01 for edge in segments))
                for edge in segments:
                    part.validateToolSweep(tool, edge.start, edge.end)

    def test_validateToolSweep_preserves_rounded_insert_contact(self):
        part = SegmentGroup()
        vertices = [(0, 0), (1, 0), (1, -0.2), (0, -0.2), (0, 0)]
        for start, end in zip(vertices, vertices[1:]):
            part.addSegment(Segment(Point(*start), Point(*end)))
        for shift in (0, 0.0025, 128):
            with self.subTest(shift=shift):
                tool = SegmentGroup()
                first = Point(-shift, -shift)
                second = Point(0.05 - shift, -shift)
                tool.addSegment(Segment(first, second, 1))
                tool.addSegment(Segment(second, first, 1))
                part.validateToolSweep(tool, Point(1.01 + shift, shift), Point(1.01 + shift, -0.2 + shift))
                for radial in (1, 0.98, 0.4):
                    with self.subTest(radial=radial):
                        position = Point(radial + shift, -0.1 + shift)
                        with self.assertRaises(RuntimeError):
                            part.validateToolSweep(tool, position, position)

    def test_validateToolSweep_rejects_crossing_containment_and_contact(self):
        part = SegmentGroup()
        tool = SegmentGroup()
        for group, vertices in (
                (part, [(0, 0), (10, 0), (10, -20), (0, -20), (0, 0)]),
                (tool, [(-0.4, -0.4), (-0.4, 2), (2, 2), (2, -0.4), (-0.4, -0.4)])):
            for start, end in zip(vertices, vertices[1:]):
                group.addSegment(Segment(Point(*start), Point(*end)))
        part.validateToolSweep(tool, Point(13, 3), Point(13, -20))
        for start, end in (((12, -10), (-3, -10)),
                           ((5, -10), (5, -10)),
                           ((10.4, -10), (10.4, -11))):
            with self.subTest(start=start, end=end):
                with self.assertRaises(RuntimeError):
                    part.validateToolSweep(tool, Point(*start), Point(*end))

    def test_isInside_rounded_square_tangent_roundoff(self):
        vertices = [(8.725, -0.4), (-3.55e-14, -0.4), (-0.4, 1.16e-14),
                    (-0.4, 8.725), (1.21e-14, 9.125), (8.725, 9.125),
                    (9.125, 8.725), (9.125, 1.07e-14), (8.725, -0.4)]
        group = SegmentGroup()
        for index, (first, last) in enumerate(zip(vertices, vertices[1:])):
            group.addSegment(Segment(Point(*first), Point(*last),
                                     0.4142135679721832 if index % 2 else 0))
        for axial in (-1, -0.43, -0.41, 9.2, 10):
            with self.subTest(axial=axial):
                self.assertFalse(group.isInside(Point(0, axial)))
                self.assertGreater(group.sdv(Point(0, axial)), 0)
        for axial in (0, 1, 8, 9):
            with self.subTest(axial=axial):
                self.assertTrue(group.isInside(Point(0, axial)))

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

    def test_sdv_measures_finite_arcs(self):
        for direction in (1, -1):
            group = SegmentGroup()
            group.addSegment(Segment(Point(0, 0), Point(2, 0), direction))
            group.addSegment(Segment(Point(2, 0), Point(0, 0)))
            for query, signed_distance in (
                (Point(1, -direction), 1),
                (Point(1, 0.75 * direction), -0.25),
                (Point(1, 2 * direction), 1),
                (Point(0, 0), 0),
            ):
                with self.subTest(direction=direction, query=(query.X, query.Z)):
                    self.assertAlmostEqual(group.sdv(query), signed_distance,
                                           places=6)

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
