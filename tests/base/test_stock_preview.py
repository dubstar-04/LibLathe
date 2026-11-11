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
