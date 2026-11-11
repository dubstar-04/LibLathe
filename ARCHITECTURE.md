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

## Cutting traversal and routing

`containment` defines the operation's machining limits, set through
`add_containment(bounds)` or `add_containment_from_limits(xmin, xmax, zmin, zmax)`.
`stock` is the optional physical material envelope, set through
`add_stock(bounds)` for safe clearance routing. These are separate bounds:
restricting containment must not shrink the stock envelope used for transfers.
All G1/G2/G3 moves, including approaches and withdrawals, stay inside
tool-reference containment. Stock-clear G0 moves may leave it for clearance.
The external router rejects missing stock-clear boundary routes transactionally;
it never converts a stock-crossing outside feed into a rapid. Without explicit
stock it uses the model's bounds. Grooving retains its prepared radial-envelope
assumption and full-model sweep checks. Boring uses separate geometric access
routing and does not claim stock-opening or holder clearance certification.

All operations inherit `pass_offset` from the base class. It is radial for
roughing/grooving, axial for facing, normal to the contour for profiling and
unused for parting. `cut_direction` is also stored and reported by `BaseOP`,
defaulting to `CutDirection.RADIAL` (`liblathe.op.base`); currently only boring uses
it to select X/Z clearing. Use `CutDirection.AXIAL` for axial clearing, not raw strings.
The add-on uses one `PassOffset` property, with descriptive
Radial Pass Offset, Axial Pass Offset or Pass Offset labels; parting hides it.
Grooving also uses `finish_pass_offset` (`FinishPassOffset` in the add-on)
between finishing contours. Previous parameter names are not supported;
existing scripts and saved operations must be updated or recreated.

Operations choose the traversal of generated geometry; the G-code router
chooses approaches and retracts. `SegmentGroup.reversed()` provides a shared,
non-mutating geometry operation that reverses segment order, endpoints and arc
bulges without changing the curve. It does not choose an operation's strategy
or rebuild its lead-in/out.

Grooving partitions its clipped finishing polyline at radial direction changes
and gaps, reversing outward runs so each stroke cuts inward. Constant-X floor
segments remain, and the existing radial router provides clearance moves
between strokes. Near-side generation followed by the existing far-side
reflection keeps both tool sides cutting toward the centerline. Other
operations retain their existing traversal and layer order.

Grooving's optional `finish_pass_offset` reserves a finishing allowance during
plunging. Each finishing contour is offset independently from the original
tool-origin profile, from the outer allowance down to `stock_to_leave`.
The default of zero preserves repeated final-contour passes.

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

## Internal boring experiment

`BoreOP` reuses defeaturing and positive offsets by mapping the target inner
contour into a finite external-material frame (`u = reference_radius - x`),
with reflected tool-relative X. Terminal extensions keep endpoint artefacts
outside the requested cutting limits. Cutting strokes return to physical X/Z
before containment clipping. The existing near/far dispatch is independent of
this material-side transformation.

The experiment confirms reuse for bounded, single-contour examples; it does not
establish support for arbitrary internal topology. External stock routing is
not reused: the operation emits a separate geometric feed entry/inward escape
sequence. Feeds stay within tool-reference containment; rapid positioning and
return may leave it to reach clearance. TurningAddon extracts coaxial internal
walls and attached floors automatically and selects one contour using containment.
There are deliberately no prepared-opening or tool-fit checks.
Clearing scans the first accessible interval of the compensated allowance region
in X (default) or Z, with at most `pass_offset` between successive scan lines.
Radial clearing's first station is containment ZMax, not the model mouth.
Stations ahead of the mouth reuse its compensated radius without changing
native extraction bounds or endpoint-limited finishing.
Separate `clearing_paths` precede `tool_paths`; the latter are reversed finishing
contours, cutting outward across the floor then toward the mouth. Each stroke
enters from containment XMin for radial clearing and finishing, feeding down
before moving outward. Axial clearing instead positions X at the exact
`containment.ZMax + clearance` plane, approaches ZMax at rapid, and feeds
axially without an engaged outward positioning feed. The same plane is used
for every front return; all known approach and return segments are checked
against target material. Withdrawal
first disengages perpendicular to the last cut before returning to XMin and
front clearance. Outward radial cuts lift in +Z (bounded by clearance,
pass spacing and containment); at the front boundary they rapid axially to
front clearance before returning inward. Axial clearing skips the inner access
lane itself, retaining space for inward disengagement. Both cutting and added
feeds are checked against the target material, not starting stock.
See [scope and limitations](docs/source/pages/operations/bore.rst).

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
