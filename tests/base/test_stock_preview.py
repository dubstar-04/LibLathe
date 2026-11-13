from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from liblathe.base.segmentgroup import StockPreview


def test_preview_snapshots_and_export():
    original = StockPreview([(0, 0), (10, 0), (10, 10), (0, 10)])
    after = original.copy()
    after.remove_feeds([(0, 0), (2, 0), (2, 2), (0, 2)], [(3, 3, 3, 3)])
    assert original.area == 100
    assert after.area == 96
    edges = after.edges()
    assert sum((x0 * z1 - x1 * z0) / 2 for x0, z0, x1, z1 in edges) == 96
    polygons = after.polygons()
    assert sum(sum(x0 * z1 - x1 * z0
                   for (x0, z0), (x1, z1) in zip(p, p[1:] + p[:1])) / 2
               for p in polygons) == 96
    assert all(not all((b[0] - a[0]) * (4 - a[1]) -
                      (b[1] - a[1]) * (4 - a[0]) > 0
                      for a, b in zip(p, p[1:] + p[:1])) for p in polygons)
    polygons.clear()
    assert after.area == 96


def test_preview_failed_removal_is_transactional():
    state = StockPreview([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(ValueError):
        state.remove_feeds([(0, 0), (2, 0), (2, 2), (0, 2)],
                           [(3, 3, 3, 3), (0, 0, float("nan"), 0)])
    assert state.area == 100


def test_preview_does_not_fill_nonconvex_input():
    with pytest.raises(ValueError):
        StockPreview([(0, 0), (4, 0), (1, 1), (0, 4)])


def test_axis_aligned_clipping_preserves_exact_boundaries():
    state = StockPreview([(0, 0), (40, 0), (40, 40), (0, 40)])
    tool = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for index, (x, z) in enumerate(((2, 8), (2, 2), (5, 8)), start=1):
        state.remove_feeds(tool, [(x, z, x, z)])
        assert state.area == 1600 - index
        assert state.uncertain_retentions == 0
        assert all(x == int(x) and z == int(z)
                   for polygon in state.polygons() for x, z in polygon)


def test_shared_preview_threaded_removals_and_readers():
    state = StockPreview([(0, 0), (40, 0), (40, 40), (0, 40)])
    tool = [(0, 0), (1, 0), (1, 1), (0, 1)]
    barrier = Barrier(4)

    def remove(row):
        barrier.wait()
        for column in range(10):
            x, z = 2 + 3 * column, 2 + 3 * row
            state.remove_feeds(tool, [(x, z, x, z)])

    def read():
        barrier.wait()
        for _ in range(30):
            snapshot = state.copy()
            edges = snapshot.edges()
            assert sum((x0 * z1 - x1 * z0) / 2
                       for x0, z0, x1, z1 in edges) == pytest.approx(snapshot.area)
            assert snapshot.polygons()
            assert snapshot.uncertain_retentions == 0
            assert 1570 <= state.area <= 1600
            assert state.polygons()
            assert state.edges()
            assert state.uncertain_retentions == 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(remove, row) for row in range(3)]
        futures.append(executor.submit(read))
        for future in futures:
            future.result(timeout=30)
    assert state.area == 1570
