import math
import random
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

import liblathe
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup


class TestDefeatureBounds(unittest.TestCase):
    @staticmethod
    def group(segments):
        group = SegmentGroup()
        for segment in segments:
            group.addSegment(segment)
        return group

    @classmethod
    def profile(cls, vertices):
        points = [Point(*vertex) for vertex in vertices]
        return cls.group([Segment(start, end)
                          for start, end in zip(points, points[1:])])

    @staticmethod
    def coordinates(group):
        return [(s.start.X, s.start.Z, s.end.X, s.end.Z, s.bulge)
                for s in group.getSegments()]

    def test_group_intersections_match_unfiltered_narrow_phase(self):
        rng = random.Random(1301)
        bulges = (0, 0, -math.tan(math.pi / 8), math.tan(math.pi / 8),
                  -1, 1, -math.tan(3 * math.pi / 8), math.tan(3 * math.pi / 8))
        for index in range(1200):
            scale = (0.01, 1, 100, 10000)[index % 4]
            origin = rng.choice((0, 1000, -1000))
            segments = [
                Segment(Point(origin + rng.uniform(-2, 2) * scale,
                              origin + rng.uniform(-2, 2) * scale),
                        Point(origin + rng.uniform(-2, 2) * scale,
                              origin + rng.uniform(-2, 2) * scale),
                        rng.choice(bulges))
                for _ in range(4)
            ]
            part, tool = segments[:2], segments[2:]
            expected = any(edge.intersect(target, False)
                           for edge in tool for target in part)
            with self.subTest(index=index, scale=scale):
                self.assertEqual(self.group(part).intersectsGroup(self.group(tool)),
                                 expected)

    def test_long_near_tangent_rounded_insert_sweep(self):
        part = self.profile([(0, 100), (20, 100), (30, 80), (30, 50)])
        part.addSegment(Segment(Point(30, 50), Point(30, 30), -1))
        part.addSegment(Segment(Point(30, 30), Point(30, 0)))
        part.addSegment(Segment(Point(30, 0), Point(0, 0)))
        vertices = [
            (12.4724569, 1.0546752, 0),
            (0.4348623, 0.0015221, 0.46630767),
            (0.0015221, 0.4348623, 0),
            (1.0546752, 12.4724569, 0.36397022),
            (1.4182909, 12.8360729, 0),
            (13.4558859, 13.8892260, 0.46630767),
            (13.8892260, 13.4558859, 0),
            (12.8360729, 1.4182909, 0.36397022),
        ]
        tool = self.group([
            Segment(Point(x, z), Point(next_x, next_z), bulge)
            for (x, z, bulge), (next_x, next_z, _) in
            zip(vertices, vertices[1:] + vertices[:1])
        ])
        for start_x, end_x in ((0.0025, 10.005), (10.005, 0.0025)):
            part.validateToolSweep(tool, Point(start_x, 100.000084),
                                   Point(end_x, 100.000084))
            for z in (100, 99.99, 99):
                with self.subTest(z=z, start=start_x):
                    with self.assertRaises(RuntimeError):
                        part.validateToolSweep(tool, Point(start_x, z), Point(end_x, z))
        for start_x, end_x in ((29.020634, 30.01), (30.01, 29.020634)):
            part.validateToolSweep(tool, Point(start_x, 30.017721),
                                   Point(end_x, 30.017721))
            for z in (30.01, 30):
                with self.subTest(z=z, start=start_x):
                    with self.assertRaises(RuntimeError):
                        part.validateToolSweep(tool, Point(start_x, z), Point(end_x, z))

    def test_arc_extrema_beyond_endpoints_are_not_pruned(self):
        for bulge in (-math.tan(math.pi / 8), math.tan(math.pi / 8),
                      -1, 1, -math.tan(3 * math.pi / 8), math.tan(3 * math.pi / 8)):
            arc = Segment(Point(1, 0), Point(0, 1), bulge)
            centre, radius = arc.getCentrePoint(), arc.getRadius()
            angle = math.atan2(arc.start.Z - centre.Z, arc.start.X - centre.X)
            for fraction in (0.37, 0.61):
                z = centre.Z + radius * math.sin(angle - 4 * math.atan(bulge) * fraction)
                line = Segment(Point(centre.X - 2 * radius, z),
                               Point(centre.X + 2 * radius, z))
                with self.subTest(bulge=bulge, fraction=fraction):
                    self.assertTrue(line.intersect(arc, False))
                    self.assertTrue(self.group([arc]).intersectsGroup(self.group([line])))

    def test_contacts_degenerate_edges_and_empty_groups(self):
        segments = [
            Segment(Point(0, 0), Point(1, 0)),
            Segment(Point(1, 0), Point(1, 1)),
            Segment(Point(0, 0), Point(0, 0)),
            Segment(Point(0, 0), Point(1, 0), 1),
            Segment(Point(0, 0), Point(1, 0), -1),
        ]
        for first in segments:
            for second in segments:
                expected = bool(second.intersect(first, False))
                self.assertEqual(self.group([first]).intersectsGroup(self.group([second])),
                                 expected)
        self.assertFalse(self.group([]).intersectsGroup(self.group(segments)))
        self.assertFalse(self.group(segments).intersectsGroup(self.group([])))

    def test_rounded_arc_contact_outside_geometric_bounds_is_retained(self):
        arc = Segment(Point(100.1, 0), Point(100, 0.1), -math.tan(math.pi / 8))
        bounds, centre = arc.Boundbox(), arc.getCentrePoint()
        line = Segment(Point(bounds.XMax + 0.0015, centre.Z - 0.2),
                       Point(bounds.XMax + 0.0015, centre.Z + 0.2))
        # Legacy radial rounding accepts this contact beyond the geometric bounds.
        self.assertGreater(line.start.X - bounds.XMax, 0.001)
        self.assertTrue(line.intersect(arc, False))
        self.assertTrue(self.group([arc]).intersectsGroup(self.group([line])))

    def test_intersection_preparation_is_refreshed_after_edits(self):
        part = self.profile([(10, 0), (10, -10)])
        tool = self.profile([(0, -5), (2, -5)])
        self.assertFalse(part.intersectsGroup(tool))
        part.addSegment(Segment(Point(1, 0), Point(1, -10)))
        self.assertTrue(part.intersectsGroup(tool))

    def groove(self):
        return self.profile([(0, 0), (10, 0), (10, -5), (6, -5),
                             (6, -11), (10, -11), (10, -18), (0, -18)])

    def assert_clear_sweeps(self, source, tool, result):
        self.assertGreater(result.count(), 0)
        for move in result.getSegments():
            for index in range(101):
                fraction = index / 100
                radial = move.start.X + (move.end.X - move.start.X) * fraction
                axial = move.start.Z + (move.end.Z - move.start.Z) * fraction
                translated = self.group([
                    Segment(Point(edge.start.X + radial, edge.start.Z + axial),
                            Point(edge.end.X + radial, edge.end.Z + axial), edge.bulge)
                    for edge in tool.getSegments()
                ])
                self.assertFalse(source.intersectsGroup(translated))
                for edge in translated.getSegments():
                    for sample in range(21):
                        along = sample / 20
                        if edge.bulge:
                            centre = edge.getCentrePoint()
                            angle = math.atan2(edge.start.Z - centre.Z, edge.start.X - centre.X)
                            angle -= 4 * math.atan(edge.bulge) * along
                            point = Point(centre.X + edge.getRadius() * math.cos(angle),
                                          centre.Z + edge.getRadius() * math.sin(angle))
                        else:
                            point = Point(edge.start.X + (edge.end.X - edge.start.X) * along,
                                          edge.start.Z + (edge.end.Z - edge.start.Z) * along)
                        self.assertFalse(source.isInside(point))
                for edge in source.getSegments():
                    self.assertFalse(translated.isInside(edge.start))

    def test_defeature_connectors_clear_the_part_and_preserve_inputs(self):
        source = self.groove()
        tool = self.profile([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
        stock = BoundBox(Point(0, 1), Point(12, -20))
        original_source, original_tool = self.coordinates(source), self.coordinates(tool)
        for grooving in (False, True):
            with self.subTest(grooving=grooving):
                result = source.defeature(stock, tool, grooving)
                self.assert_clear_sweeps(source, tool, result)
                if grooving:
                    self.assertLess(min(edge.end.X for edge in result.getSegments()), 7)
                self.assertEqual(self.coordinates(source), original_source)
                self.assertEqual(self.coordinates(tool), original_tool)

    def test_defeature_samples_are_available_without_changing_the_contour(self):
        source = self.groove()
        tool = self.profile([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
        stock = BoundBox(Point(0, 1), Point(12, -18))

        result = source.defeatureWithSamples(stock, tool, True)
        reference = source.defeature(stock, tool, True)

        self.assertEqual(self.coordinates(result.contour), self.coordinates(reference))
        self.assertGreater(len(result.samples), 1)
        self.assertTrue(all(first.Z > second.Z
                            for first, second in zip(result.samples, result.samples[1:])))
        for sample in result.samples:
            source.validateToolSweep(tool, sample, sample)

        ordinary = source.defeatureWithSamples(stock, tool, False).samples
        grooved = result.samples
        self.assertTrue(all(next_point.X >= point.X - 1e-5
                            for point, next_point in zip(ordinary, ordinary[1:])))
        self.assertTrue(any(next_point.X < point.X - 1e-5
                            for point, next_point in zip(grooved, grooved[1:])))

    def test_expanded_containment_certifies_long_rounded_insert_connectors(self):
        source = self.profile([(0, 95.005), (22, 95.005), (22, 0), (0, 0)])
        vertices = [(0.2, 2), (0, 1.8), (0, 0.2), (0.2, 0),
                    (12, 0), (12, 2), (0.2, 2)]
        tool = self.group([
            Segment(Point(*start), Point(*end),
                    -math.tan(math.pi / 8) if index in (0, 2) else 0)
            for index, (start, end) in enumerate(zip(vertices, vertices[1:]))
        ])
        result = source.defeature(BoundBox(Point(0, 0), Point(30, 100)), tool, False)
        self.assertGreater(result.count(), 0)
        for move in result.getSegments():
            source.validateToolSweep(tool, move.start, move.end)

    def test_defeature_retains_the_curved_tool_footprint(self):
        source = self.groove()
        linear = self.profile([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
        curved = self.group([Segment(edge.start, edge.end, 0.5 if i == 0 else 0)
                             for i, edge in enumerate(linear.getSegments())])
        stock = BoundBox(Point(0, 1), Point(12, -20))
        for grooving in (False, True):
            with self.subTest(grooving=grooving):
                result = source.defeature(stock, curved, grooving)
                self.assertNotEqual(self.coordinates(result),
                                    self.coordinates(source.defeature(stock, linear, grooving)))
                self.assert_clear_sweeps(source, curved, result)

    def test_contained_and_translated_inserts_have_clear_start_and_connectors(self):
        source = self.profile([(0, 0), (10, 0), (10, -20), (0, -20)])
        stock = BoundBox(Point(0, 3), Point(12, -20))
        for shift in (0, -0.6):
            tool = self.profile([(radial + shift, axial - shift) for radial, axial in
                                 ((0.2, -0.2), (2, -0.2), (2, -2), (0.2, -2), (0.2, -0.2))])
            with self.subTest(shift=shift):
                result = source.defeature(stock, tool, False)
                self.assertGreater(result.getSegments()[0].start.Z, 2 + shift)
                self.assert_clear_sweeps(source, tool, result)

    def test_defeature_limits_follow_tool_reference_translation(self):
        source = self.profile([(0, 0), (10, 0), (10, -20), (0, -20)])
        stock = BoundBox(Point(0, 3), Point(12, -20))
        vertices = ((0, -1), (0, 1), (2, 1), (2, -1), (0, -1))
        original = source.defeature(stock, self.profile(vertices), False).boundbox()
        radial_shift, axial_shift = 0.6, 0.8
        shifted_tool = self.profile([(radial - radial_shift, axial - axial_shift)
                                     for radial, axial in vertices])
        shifted = source.defeature(stock, shifted_tool, False).boundbox()
        self.assertAlmostEqual(shifted.ZMin - axial_shift, original.ZMin, delta=0.02)
        self.assertAlmostEqual(shifted.ZMax - axial_shift, original.ZMax, delta=0.02)
        self.assertAlmostEqual(shifted.XMax - radial_shift, original.XMax, delta=0.02)

    def test_rounded_insert_reference_preserves_defeature_contour(self):
        source = self.profile([(0, 0), (10, 0), (10, -20), (0, -20)])
        stock = BoundBox(Point(0, 1), Point(12, -20))
        corner = -math.tan(math.pi / 8)
        outline = [(0, 0.4, 0.4, 0, corner), (0.4, 0, 9.125, 0, 0),
                   (9.125, 0, 9.525, 0.4, corner), (9.525, 0.4, 9.525, 9.125, 0),
                   (9.525, 9.125, 9.125, 9.525, corner), (9.125, 9.525, 0.4, 9.525, 0),
                   (0.4, 9.525, 0, 9.125, corner), (0, 9.125, 0, 0.4, 0)]
        contours = []
        for shift in (0, 0.4):
            tool = self.group([Segment(Point(radial - shift, axial - shift),
                                       Point(end_radial - shift, end_axial - shift), bulge)
                               for radial, axial, end_radial, end_axial, bulge in outline])
            result = source.defeature(stock, tool, False)
            contours.append([Segment(Point(edge.start.X - shift, edge.start.Z - shift),
                                     Point(edge.end.X - shift, edge.end.Z - shift))
                             for edge in result.getSegments()])
        for original, shifted in (contours, reversed(contours)):
            for edge in original:
                for sample in range(41):
                    point = edge.start.lerp(edge.end, sample / 40)
                    self.assertLessEqual(min(candidate.distanceToPoint(point) for candidate in shifted), 0.02)

    def test_defeature_search_reaches_tool_origin_clearance(self):
        source = self.profile([(0, 0), (10, 0), (10, -18), (0, -18)])
        stock = BoundBox(Point(0, 2), Point(12, -20))
        original_source = self.coordinates(source)
        for reference_x in (-0.4, 0, 0.4, 1.0):
            tool = self.profile([(radial - reference_x, axial) for radial, axial in
                                 ((0, -1), (0, 1), (2, 1), (2, -1), (0, -1))])
            original_tool = self.coordinates(tool)
            with self.subTest(reference_x=reference_x):
                result = source.defeature(stock, tool, False)
                cuts = [segment for segment in result.getSegments()
                        if abs(segment.start.X - segment.end.X) < 0.02
                        and abs(segment.start.Z - segment.end.Z) > 5]
                self.assertTrue(cuts)
                for segment in cuts:
                    self.assertAlmostEqual(segment.start.X, 10 + reference_x, delta=0.02)
                    self.assertAlmostEqual(segment.end.X, 10 + reference_x, delta=0.02)
                self.assertEqual(self.coordinates(source), original_source)
                self.assertEqual(self.coordinates(tool), original_tool)

    def test_radial_scan_reports_unrepresentable_step_instead_of_looping(self):
        # At X = 2**17 the 0.005 float radial step rounds away; run isolated so a hang fails.
        script = textwrap.dedent("""
            from liblathe.base.boundbox import BoundBox
            from liblathe.base.point import Point
            from liblathe.base.segment import Segment
            from liblathe.base.segmentgroup import SegmentGroup

            def profile(vertices):
                group = SegmentGroup()
                points = [Point(*vertex) for vertex in vertices]
                for start, end in zip(points, points[1:]):
                    group.addSegment(Segment(start, end))
                return group

            part = profile([(0, 0), (10, 0), (10, -20), (0, -20)])
            tool = profile([(radial - 131072, axial) for radial, axial in
                            ((0, -1), (0, 1), (2, 1), (2, -1), (0, -1))])
            try:
                part.defeature(BoundBox(Point(0, 2), Point(12, -20)), tool, False)
            except RuntimeError as error:
                print(error)
            else:
                print("no error")
        """)
        # Import the same liblathe build as this process, not an unbuilt source checkout.
        root = Path(liblathe.__file__).resolve().parents[1]
        try:
            result = subprocess.run([sys.executable, "-c", script], cwd=root, capture_output=True,
                                    text=True, timeout=30)
        except subprocess.TimeoutExpired:
            self.fail("Radial defeature scan did not advance at coordinate precision")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Cannot advance radial defeature scan at coordinate precision", result.stdout)


if __name__ == '__main__':
    unittest.main()
