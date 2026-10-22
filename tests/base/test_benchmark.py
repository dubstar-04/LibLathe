import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from examples import benchmark
from examples import ex4_performance


class test_Benchmark(unittest.TestCase):
    def test_measure_excludes_warmups_and_reports_percentiles(self):
        operation = Mock(return_value=7)
        with patch.object(benchmark.time, 'perf_counter',
                          side_effect=[10, 11, 20, 23, 30, 32]):
            result, report = benchmark.measure(
                operation, lambda value: {'output_segments': value}, 1, 3)
        self.assertEqual(operation.call_count, 4)
        self.assertEqual(result, 7)
        self.assertEqual(report, {
            'output_segments': 7, 'median_seconds': 2, 'p95_seconds': 3,
            'samples_seconds': [1, 3, 2],
        })

    def test_measure_rejects_changed_output_counts(self):
        operation = Mock(side_effect=[2, 3])
        with self.assertRaisesRegex(RuntimeError, 'Benchmark output changed'):
            benchmark.measure(operation, lambda n: {'output_segments': n}, 1, 2)

    def test_workload_shapes_and_multipliers(self):
        group = ex4_performance.create_profile()
        self.assertEqual(group.count(), 24)
        dense = benchmark.subdivide_lines(group, 16)
        self.assertEqual(dense.count(), 384)
        self.assertTrue(dense.getSegments()[0].start.isSame(group.getSegments()[0].start))
        self.assertTrue(dense.getSegments()[-1].end.isSame(group.getSegments()[-1].end))
        scaled = ex4_performance.create_profile(8).boundbox()
        bounds = group.boundbox()
        for field in ('XMin', 'XMax', 'ZMin', 'ZMax'):
            self.assertAlmostEqual(getattr(scaled, field),
                                   8 * getattr(bounds, field), delta=1e-4)
        arcs = benchmark.arc_profile().getSegments()
        self.assertGreater(sum(s.bulge != 0 for s in arcs), len(arcs) / 2)
        with self.assertRaisesRegex(ValueError, 'line-only'):
            benchmark.subdivide_lines(benchmark.arc_profile(), 16)

    def test_cli_outputs_json_and_renders_without_viewer(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, 'examples/benchmark.py', '--build-type', 'RelWithDebInfo',
             '--cases', 'example', '--repetitions', '2', '--render'],
            cwd=root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['schema_version'], 1)
        self.assertEqual(report['environment']['build_type'], 'RelWithDebInfo')
        self.assertEqual(report['environment']['python_version'],
                         benchmark.platform.python_version())
        self.assertEqual(report['settings']['repetitions'], 2)
        self.assertEqual(report['settings']['warmups'], 1)
        self.assertEqual(report['settings']['p95_method'], 'nearest_rank')
        self.assertTrue(report['settings']['rendering'])
        case, = report['cases']
        self.assertEqual(case['defeature']['input_segments'], 24)
        self.assertEqual(case['defeature']['output_segments'], 15)
        self.assertEqual([o['distance'] for o in case['offsets']], [1, 2, 3, 4])
        self.assertEqual([o['output_segments'] for o in case['offsets']], [45, 49, 61, 62])
        for stage in [case['defeature'], *case['offsets'], case['render']]:
            self.assertEqual(len(stage['samples_seconds']), 2)
            self.assertGreaterEqual(stage['p95_seconds'], stage['median_seconds'])
        self.assertGreater(case['render']['width'], 0)
        self.assertGreater(case['render']['height'], 0)

    def test_cli_rejects_insufficient_runs_before_running_geometry(self):
        for options in (['--warmups', '0'], ['--repetitions', '1']):
            with self.subTest(options=options), patch.object(benchmark, 'run_case') as run:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        benchmark.main(['--build-type', 'RelWithDebInfo', *options])
                self.assertEqual(error.exception.code, 2)
                run.assert_not_called()

    def test_example_keeps_interactive_and_headless_modes(self):
        with patch.object(ex4_performance.Debug, 'draw') as draw:
            with contextlib.redirect_stdout(io.StringIO()):
                interactive = ex4_performance.main()
                headless = ex4_performance.main(headless=True)
            draw.assert_called_once_with(interactive)
        self.assertEqual([g.count() for g in interactive],
                         [g.count() for g in headless])

    def test_preview_renderer_returns_an_image_without_showing_it(self):
        with patch('PIL.Image.Image.show') as show:
            image = benchmark.Debug().render([ex4_performance.create_profile()])
            try:
                self.assertEqual(image.size, (1360, 460))
                show.assert_not_called()
            finally:
                image.close()
