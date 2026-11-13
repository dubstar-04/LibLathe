# Architecture: profile offsetting

LibLathe turns part profiles into tool-accessible paths and offset contours
for machining. The current approach combines defeaturing, a signed distance
field and adaptive quadtree sampling.

## Profiles and coordinates

Profiles are ordered, connected chains of lines and arcs. X represents radius
and Z represents position along the lathe axis. In the plotted lathe view,
Z increases to the right and positive X increases downward from the centreline.

The distance field needs a closed region. Open profiles close from their
endpoints to the axis and along it; endpoints at the same Z close directly.
Already closed profiles need no additional boundary. Profiles and their closure
must form a simple region.

## Processing pipeline

1. **Defeature the profile.** Move the tool footprint along the profile and find
   the first non-intersecting position at each sample. This removes inaccessible
   features; the grooving setting controls whether the path may move back inward.
   Cached segment bounds reject disjoint pairs before detailed intersection
   checks, without changing traversal order.

2. **Prepare the distance field.** Build a boundary snapshot containing the
   profile, its closure and reusable arc data. Distance comes from the nearest
   finite line or arc; ray crossings determine the sign. Values are negative
   inside, zero on the boundary and positive outside. Positive offsets expand
   the region, while negative offsets move inward.

3. **Sample with a quadtree.** Cover the profile and requested offset with a
   padded search region. Subdivide cells that could contain the target distance
   level, rejecting cells by unsigned distance before calculating their sign.
   Project leaf-centre and corner samples onto that level, refining projections
   when the nearest boundary feature changes.

4. **Build the contour.** Keep machining candidates from the original profile,
   not the artificial closure. Remove duplicates, order points by greedy
   nearest neighbour and simplify the resulting polyline with
   Ramer-Douglas-Peucker. A spatial index accelerates neighbour searches without
   changing the greedy rule or its tie-breaking.

5. **Validate the result.** Check connecting chords before and after
   simplification against the requested signed-distance level. Reject
   uncertifiable contours and detected collapsed, zero-width branches rather
   than returning an inaccurate path.

Prepared geometry prunes straight-edge queries against cached segment bounds.
A point-to-box squared-distance lower bound rejects lines that cannot improve
the current nearest-point result, preserving original traversal order on ties.
Vertical-ray classification skips lines outside the query's X range or below
its Z coordinate. Arcs retain the existing unpruned narrow-phase calculations;
no tolerance, scan-grid or sweep-validation changes accompany this optimization.

## Cutting traversal and routing

`containment` defines the operation's machining limits, set through
`add_containment(bounds)` or `add_containment_from_limits(xmin, xmax, zmin, zmax)`.
`stock` is the optional physical material envelope, set through
`add_stock(bounds)` for initial clearance positioning. These are separate bounds.
All G1/G2/G3/G33 moves, including approaches and withdrawals, stay inside
tool-reference containment. G0 transfers stay outside its interior, but may
cross the original stock envelope to reach its boundary. Users evaluate remaining
stock before machining; advisory previews do not approve routes. Protected
routes retain full-insert finished-part sweep checks, and missing boundary access
fails transactionally. Without explicit stock, initial clearance uses model bounds.
Internal Rough/Profile routing enters from the axis-side containment boundary
and checks protected moves against the selected internal contour. It does not
certify a pre-existing opening or bar/holder clearance.

All operations inherit `pass_offset` from the base class. It is radial for
roughing/threading, normal to the contour for profiling and unused for parting.
Rough directions `-Z` and `+Z` make axial passes; `Radial` makes one full radial
stroke per axial station and covers facing and groove roughing. Facing ends in
a +Z pull-off; groove-enabled strokes withdraw radially through the plunge.
External grooving repositions at containment-based clearance between passes,
with global stock/model clearance only at operation entry and final return.
The local lane must be prepared; remaining stock is not automatically certified.
Profile supports `-Z`, `+Z` and Radial
traversal. Rough and Profile expose External/Internal mode. Previous operation
classes and parameter names are not supported; existing scripts and saved
operations must be updated or recreated.

Operations choose the traversal of generated geometry; the G-code router
chooses approaches and retracts. `SegmentGroup.reversed()` provides a shared,
non-mutating geometry operation that reverses segment order, endpoints and arc
bulges without changing the curve. It does not choose an operation's strategy
or rebuild its lead-in/out.

`BaseOP` owns shared input/parameter validation, path-state reset and an ordered
routing wrapper. Each strategy still chooses its groups, traversal order and
routing policy explicitly. Parting remains an unprotected stock-removal cut and
explicitly requests radial withdrawal through the kerf. Centreline drilling
retains separate access routing. Generation publishes complete path sets only;
validation and routing failures clear both published collections. Unused
cutting parameters are not validated, and feed rates remain pass-through.

`SegmentGroup.reflectX(radius=0)` provides the common native transformation
`X = radius - X` for side dispatch and Internal mode. It preserves segment
order, reverses arc bulges and does not mutate its input.

Radial Profile partitions external clipped contours at gaps and radial
direction changes, reversing outward runs toward their floor. In Internal mode
it traverses each connected bore contour from bottom toward mouth as the exact
reverse of the `-Z` pass, leads included. Groove
roughing and finishing use separate Rough and Profile operations with no
groove-specific finish-stepdown parameter.

Full-insert sweep checks certify finishing cuts as well as added approach and
retract moves. Long public sweep queries are partitioned into consecutive
translations no longer than the insert's smaller X/Z extent; each uses the
existing checker and subdivision budget. This bounds the work of individual
checks without skipping any travel or relaxing clearance tolerances.
Swept insert bounds that are separated from the complete part bounds by the
numerical margin certify clearance directly. This avoids unnecessary subdivision
for long moves just above a flat face; overlapping envelopes still use the
adaptive full-insert checks.
Within those checks, patch bounds are also compared with an arc's supporting
circle. A patch wholly inside or outside that circle cannot intersect the arc,
even when its rectangular bounds overlap. This avoids excessive subdivision
near curved groove shoulders while retaining the numerical clearance margin.

`SegmentGroup.validateToolSweeps(tool, moves)` batches ordered straight
translations against one immutable part/tool snapshot. It uses the scalar
checker without reducing tolerances or skipping moves, and identifies the first
failed move by index and coordinates. Profile and Rough generation use batches;
routing keeps individual queries because candidate selection depends on each
result. Both APIs retain the GIL. Snapshots live only for the call, avoiding
mutable cross-call caches. Rebuild the native modules together before using the
Python operation changes.

## Internal machining mode

Rough and Profile share an Internal frame in `BaseOP`. It maps selected part
geometry and containment with `X' = R - X`, reflects the tool-relative X
coordinates, plans using the ordinary reachable-profile/contour strategies,
then maps paths and G-code back to physical X. Arc offsets are reflected and
clockwise/counter-clockwise commands are exchanged. This frame is composed
after Near/Far normalization; it does not mutate caller geometry or change the
physical Near/Far sign convention.

Internal routes use the axis-side containment boundary as their radial access
lane. This avoids routing the tool reference through negative radii when the
selected containment reaches the spindle axis. The selected internal contour
and protected feed sweeps are checked, but stock-opening, tool-fit, holder,
fixture and machine-travel checks are deliberately not inferred. TurningAddon
extracts one coaxial inner contour and any attached inward floor from the job
model using X/Z containment. Stock preview consumes the physical-coordinate
insert and feeds after planning, not the reflected computational frame.

## External threading

`ThreadOP` reuses the base lifecycle and signed-side dispatch, but emits explicit
spindle-synchronized G33 strokes rather than using the ordinary feed router. Radial passes
share a synchronized Z start/end and K lead; spring passes repeat the final depth.
G18/G90/G8 make the generated radius-coordinate program explicit. Spindle settings
and synchronization hardware remain the caller's responsibility.

Containment specifies tool-reference crest/root radii and the complete synchronized
stroke, including prepared run-in/out space. Full-insert checks certify the deepest
radial entry against the unthreaded part, and the deepest pass and withdrawal against
the part with the containment thread band removed; the threading cuts intentionally
enter the unthreaded model and do not claim final-thread surface certification.
The ordinary XZ plot displays pass projections only. Axisymmetric stock subtraction
cannot represent helical threads and must not consume G33 as ordinary turning feeds.
See [threading setup and limitations](docs/source/pages/operations/thread.rst).

## Advisory remaining stock

`DrillOP` is a separate centreline routing strategy, not an insert offsetting
operation. It inherits the shared parameter/geometry storage but bypasses signed
tool-side dispatch, model extraction and external routing: X stays zero and
explicit G0/G1 commands use drill-tip depths. `Drill` supplies a symmetric
convex meridional footprint. It therefore uses the same stock subtraction API
as insert operations without a drilling-specific Boolean engine.

`StockPreview` consumes the physical insert and already-generated cutting feeds.
Its shared native convex-cell subtraction handles external cuts and bore-created
cavities without operation dispatch or a reflected internal-material frame.
Radial/axial boring and near/far sides use the same API; resulting snapshots
carry forward to following operations without becoming planner input.
Convexity is required for initial stock and inserts, not for the remaining
material. Numerically unresolved clipping retains material and reports it;
this is not an exact or clearance-certified Boolean model.
TurningAddon starts from the stock's outer rotational envelope, closed to the
axis, so pre-existing openings are not represented. Generated-feed subtraction
can create holes; it cannot infer a pilot hole or certify tool access.
See [remaining-stock guide](docs/source/pages/remaining_stock.rst).

## Geometry lifetime and debug data

Prepared geometry belongs to one extraction and is rebuilt for each request,
so source edits cannot leave stale cached data. Quadtree nodes are recorded as
flat snapshots rather than retained child trees. Debug retrieval returns
independent node copies and resolves any deferred signs against the geometry
used for that extraction.

## Trade-offs

The distance field provides one approach for outward, zero and inward offsets,
including corners and concave regions, without constructing analytic joins.
However, output is a polyline: original arcs are not retained, and connectivity
is reconstructed from sampled points.

Accuracy checks do not guarantee that every small feature or contour component
is found. Sampling and greedy ordering remain limitations around narrow or
disconnected features. Defeaturing may remove inaccessible features before
offsetting, so machining workflows and direct offset queries have different
coverage requirements.

## Alternative techniques

- **Envelope or Minkowski-sum construction:** derive reachable or offset
  boundaries from geometric primitives. This can retain arcs, but requires
  careful treatment of profile reversals, tool shape and disappearing features.
- **Analytic offsets with distance filtering:** offset primitives, construct
  joins and trim unwanted pieces. Connectivity and self-intersections are the
  main challenges.
- **Marching squares:** extract connected contours from the sampled distance
  field instead of ordering projected points. Ambiguous cells and transitions
  between quadtree depths require special handling.
- **Voronoi or medial-axis methods:** derive offsets from nearest-feature
  relationships. These offer a more geometric construction at the cost of
  greater implementation complexity.
- **Adaptive leaf sizes:** use fewer samples where the boundary is simple,
  while accounting for changes in nearest feature and uneven point spacing.
