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
