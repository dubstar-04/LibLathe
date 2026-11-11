Remaining-stock guide
=====================

``liblathe.base.segmentgroup.StockPreview`` predicts 2D material remaining
after already-generated cutting feeds. It is advisory only: it does not change
toolpaths, plan rest machining, approve rapids or certify machining safety.
It uses the existing native extension and adds no dependencies.

Python usage
------------

Stock and insert outlines are simple convex polygons, supplied as ordered
``(x, z)`` vertices without a repeated closing vertex. X is radius, not diameter.
Tool vertices are relative to the same tool origin used by the generated moves.
Stock, tools and moves must share one physical coordinate system.

.. code-block:: python

   from liblathe.base.segmentgroup import StockPreview

   original = StockPreview([(0, 0), (20, 0), (20, 50), (0, 50)])
   before = original.copy()
   after = before.copy()
   insert = [(0, 0), (2, 0), (2, 2), (0, 2)]
   feeds = [(18, 51, 18, 3), (16, 51, 16, 3)]
   after.remove_feeds(insert, feeds)

   print(original.area, after.area)  # square model units
   edges = after.edges()            # unordered (x0, z0, x1, z1)
   polygons = after.polygons()      # independent convex material cells
   print(after.uncertain_retentions)

``remove_feeds`` mutates only the receiving snapshot. Each move contains
``(start_x, start_z, end_x, end_z)`` and represents a straight translation of the
whole insert. Failed removal leaves the snapshot unchanged. Pass ``after.copy()``
to the next calculation to retain independent before/after snapshots.
Python preview methods retain the GIL, serializing access to each snapshot
between Python threads, including the transactional copy and replacement during
removal. A sequence of separate calls is not atomic; use ``copy()`` when reading
several properties of one consistent snapshot.

Include cutting feeds, including feed approaches and withdrawals; do not subtract
rapid moves. Track position through both rapids and feeds when extracting moves
from generated commands. Resolve modal coordinates and units first, and reject
unsupported motion rather than silently ignoring it. Arc motion is not supported.

Plotting
--------

Convert exported edges into a ``SegmentGroup`` for the existing ``Plot``:

.. code-block:: python

   from liblathe.base.point import Point
   from liblathe.base.segment import Segment
   from liblathe.base.segmentgroup import SegmentGroup
   from liblathe.debug.plot import Plot

   boundary = SegmentGroup()
   for x0, z0, x1, z1 in after.edges():
       boundary.addSegment(Segment(Point(x0, z0), Point(x1, z1)))
   plot = Plot()
   plot.backplot([boundary])

The existing roughing example includes tool sampling, feed extraction,
boundary-area validation and plotting:

.. code-block:: sh

   python examples/ex3_rough_op.py --no-show

It saves ``rough_remaining_stock.png``, ``rough_toolpath.jpg`` and
``profile.gcode`` in the examples directory. Use ``--output`` with an existing
directory to keep generated files elsewhere. The original stock boundary is
included for context and consistent plot bounds, including fully removed stock.
For filled rendering, use ``polygons()`` rather than joining unordered edges;
the disjoint material cells preserve removed pockets and disconnected pieces.

Internal boring
---------------

Generated bore feeds use this same physical-coordinate subtraction, with no
operation-specific material transform or internal-stock algorithm. Both radial
and axial clearing, finishing, and near/far tool sides are supported. The bore
planner's reflected computational frame must not be used for stock subtraction:
use the actual insert and emitted moves in one common coordinate system.
Subsequent operations consume the resulting stock snapshot in the usual way.
The preview remains downstream of planning and does not validate prepared-hole
access, entry, rapids or bar/holder fit.

TurningAddon initializes this preview from the stock's outer rotational envelope,
closed to the spindle axis. Pre-existing openings in hollow/imported stock are
not represented, even though holes created by subtracting generated feeds are.
Convex validation checks the supplied envelope, not the original solid topology.

Representation and limitations
------------------------------

The shared C++14 core in ``liblathe/base/stockstate.h`` represents stock as
disjoint convex polygon cells. A straight convex insert sweep is the convex hull
of its endpoint positions. Half-plane subtraction partitions intersected cells;
bounds and intersection rejection avoid unnecessary fragmentation.

- Initial stock and inserts must be convex. Concave inputs and imported stock
  holes are unsupported; subtraction can produce holes and disconnected stock.
- Only straight translations are supported, without tool rotation or arc sweeps.
  The roughing example approximates insert curves with inscribed chords using
  0.005 model-unit sagitta. This is display approximation, not a safety bound.
- Floating-point predicates are not a certified conservative Boolean engine.
  Numerically unresolved fragments retain their original cell and increment
  ``uncertain_retentions``. This may overestimate remaining stock.
- Strict idempotence and an overall approximation-error bound are not guaranteed:
  repeated sweeps can refine previously retained material. A repeated-pawn
  stress experiment changed area by about 0.006 square model units.
- Boundary export cancels opposite shared spans, including T junctions, using
  a 1e-12 model-unit tolerance. Edges have material on their left but are
  unordered, not validated watertight outer/hole loops.
- Boundary export is quadratic in cell-edge count; removal scans cells with
  bounding-box rejection. Highly fragmented histories need further benchmarking.
- No persistence, 3D stock, rest machining or stock-based rapid approval exists.

Typical captured roughing/profile experiments took approximately 1--15 ms for
removal and 0.3--3 ms for boundary export, excluding path generation, Python
startup and plotting. These are illustrative measurements, not guarantees.

Validation
----------

Python binding tests run with the normal suite:

.. code-block:: sh

   python -m pytest tests/base/test_stock_preview.py tests/op/test_bore_stock_preview.py -q

Generated-operation tests cover radial/axial boring, near/far sides and blind/
through contours. They check cavity removal, preservation of the outer wall and
blind-floor allowance, snapshot independence, boundary area and unchanged paths.
FreeCAD integration was also compared with independent planar OCC subtraction
of the same sampled insert sweeps, including following-operation snapshots and
the filled preview. Numerically uncertain retention caused excess material of
approximately 0.067 mm2 (radial) and 1.592 mm2 (axial) in the captured 5500 mm2
stock section; these are observations, not accuracy guarantees. Tool-side
reflection can change numerical retention even for equivalent physical cuts.

The native geometry tests cover snapshots, pockets, repeated and adjacent cuts,
disconnected pieces, tangencies, narrow remnants, uncertain retention and
20,000 seeded occupancy queries:

.. code-block:: sh

   g++ -std=c++14 -O3 -Wall -Wextra -Werror tests/native/stock_preview.cpp -o /tmp/stock-preview-tests
   /tmp/stock-preview-tests

For sanitizer validation, add ``-fsanitize=address,undefined
-fno-omit-frame-pointer`` to the compiler command.
