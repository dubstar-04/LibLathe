# Architecture: profile offsetting

This document records how LibLathe offsets profiles today, the alternatives
considered, and the trade-offs of each. It is a high-level decision aid, not a
commitment to a particular alternative or a record of benchmark results.
See [PLAN.md](PLAN.md) for the correctness and performance work in progress.

## Problem

Part profiles are ordered, connected chains of lines and arcs in X (radius)
and Z (axis). Open profiles close radially from their endpoints to X = 0 and
along the axis; the resulting boundary must form a simple region. Inputs may
start off the axis, as offset results can do. Already closed profiles add no
edges; endpoints at the same Z close directly without overlapping axis spurs.
In the plotted lathe view, Z is horizontal and positive X increases downward
from the centreline. Operations need:

- an outward offset by a step-over or stock-to-leave distance;
- a small inward offset, used to check toolpaths against the part;
- defeaturing: the reachable path of a tool, with undercuts removed.

Outputs must be connected, ordered paths suitable for gcode. Inputs are small
(tens of segments), so robustness matters more than asymptotic speed.

## Current design

1. **Defeature:** step the tool shape along Z in 0.01 increments and, at each
   step, search X for the first position where the tool does not intersect the
   part.
2. **Offset:**
   - Evaluate a signed distance field against that complete boundary: negative
     inside, zero on it, positive outside. Sign uses half-open ray crossings;
     distance and projection use the nearest finite line or arc, including the
     artificial closing edges.
   - Expand the search root by the offset magnitude plus one leaf-width margin,
     so its half-open maximum edges do not clip the contour. Keep its lower X
     bound at the axis (or the profile's X minimum if negative); the start-Z
     output clip is independent of the root.
   - Subdivide a quadtree where `|distance - offset|` is within the cell's
     half-diagonal, down to 0.05 cell width.
   - Project each leaf centre and corner onto its nearest boundary point and move it
     towards the centre by the offset's magnitude. Exclude candidates owned by
     artificial closing edges, including when closure becomes nearer after
     projection. Original geometry wins exact ties, so explicitly supplied
     faces remain eligible. Retain the first segment's start-Z clip.
     Zero levels accept centres from either side. Signed nearest-feature
     projection repeats for at most eight iterations when the nearest feature
     changes; candidates are retained only if their SDF residual is within
     `1e-5 + 4 * float_epsilon * max(1, |X|, |Z|, |offset|)`.
   - Allow float-rounding slack at shared leaf edges so adjacent rounded cell
     centres cannot leave an unsampled crack. Remove coincident samples before
     ordering. Start on the retained contour's highest Z, breaking ties by
     distance to the original start; starting at the nearest point to that
     original start can incorrectly begin inside a groove.
   - Order the points by greedy nearest neighbour, then simplify with
     Ramer-Douglas-Peucker (tolerance 0.01). The public offset operation removes
     adjacent coincident samples using the existing five-decimal point
     comparison before checking that at least two distinct points remain.
   - Validate both raw and simplified connecting chords against the requested
     signed-distance level with a total error budget of **0.05 model units**.
     Reject detected zero-width branches instead of connecting them into the path.

The distance-field domain and the extracted machining profile are deliberately
different: the field includes the complete closed boundary, but output omits
artificial-closure candidates. Closure can therefore change where inward
offsets terminate. Chord validation bounds signed-distance error, but does not
prove that every contour component is present or that ordering is topologically
correct for every input.

Debug nodes are recorded once as flat snapshots while visiting the quadtree.
Subdivision recurses over local nodes rather than retaining child subtrees.
`getNodes()` returns independent snapshots in the same root-first depth-first
order, with unchanged `center`, `width`, `height` and `sdv` fields. Before
extraction, including after reinitialisation, it returns just the root. This
avoids recursively copying descendants and the growing output vector merely
to draw the tree; offset accuracy and sampling are unchanged.

### Accuracy and topology

The agreed complete-contour target is **0.05 model units**, not 0.05 diameter
units or an additional machining clearance. The production guard uses the
closed field's 1-Lipschitz property: midpoint residual plus the distance to the
farther endpoint bounds the entire chord. It bisects until that bound, including
float/arc-rounding allowance, fits the budget. It raises `RuntimeError` if a
sample exceeds the budget or coordinate precision prevents certification.
This guard runs before and after RDP; RDP's tolerance remains 0.01 and does not
add another 0.01 to the final allowed error.

Nonzero-level vertices are also checked for equidistant, opposing nearest
boundary normals. These identify collapsed, zero-width branches such as a
rectangular groove offset by half its width. Such contours raise an explicit
error; no topology-repair fallback is attempted. This is a degeneracy check,
not a general topology validator.

Accuracy and coverage are separate concerns: a contour can contain accurate
points while missing a groove, loop or entire component. Validation therefore
needs to consider both connecting segments and expected contour coverage.
Arbitrarily small features and global contour completeness are not guaranteed;
supported profiles must still form a simple region with their closure.
Defeaturing can remove inaccessible grooves before offsetting, so machining
workflows and direct offset queries have different feature requirements.

**Pros**
- The field represents corners, concave regions and negative levels without
  constructing analytic offset joins; extraction still depends on sampling
  and ordering.
- One method serves any offset distance and sign.
- Accepted projections are checked against the requested signed distance.

**Cons**
- Produces a polyline; connectivity is reconstructed by greedy ordering,
  which can jump between branches in narrow features.
- Work scales with cell size rather than geometry; straight edges are sampled as
  densely as curves.
- Arcs are lost: output is a polyline thinned by RDP.
- A point is dropped silently if its projection lands outside its own cell.
- Accuracy depends on the distance field being exact. The review found sign and
  arc-distance bugs (see PLAN.md).

## Alternatives

### 1. Upper envelope / Minkowski sum

A turned part is the region 0 <= X <= f(Z), so its profile is a function of Z.
The outward offset is then the upper envelope of the offsets of its pieces:
lines become parallel lines, convex vertices become arcs of radius `d`, then take
the maximum over Z. Inward offsets use the lower envelope. The same idea applies
to defeaturing, which is the Minkowski sum of the profile with the tool shape.

**Pros**
- Exact, and keeps arcs.
- No distance field, topology or ordering problem; O(n log n).
- Steps, shoulders and radial grooves are still functions of Z, so they are
  handled.
- Could replace the 0.01 stepping used by defeaturing.

**Cons**
- Cannot represent a profile that reverses in Z, such as a groove cut into a
  face, a bore or a dovetail. Defeatured profiles never do this.
- The offset must still extend beyond the profile's Z range and follow the
  existing start-plane and axis rules.
- Inward offsets are not a simple mirror: convex vertices stay sharp, concave
  ones become arcs, and thin features can vanish.
- An asymmetric tool needs a convex tool shape or a convex decomposition, and
  results differ from the stepped 0.01 version by up to about that amount.

### 2. Analytic raw offset with distance filtering

Offset each primitive, join the pieces, and keep only the parts at least `d` from
the original profile.

**Pros**
- Works for any profile and keeps arcs.
- Connected output; the existing distance function does the trimming.

**Cons**
- Joins and self-intersections must be handled correctly, which is where this
  kind of code usually fails.
- The filter is only as reliable as the distance function.

### 3. Marching squares on the adaptive grid

Keep the quadtree but extract contours by interpolating the distance at cell
corners instead of projecting leaf centres.

**Pros**
- Connected output without nearest-neighbour ordering.
- Reuses the existing sampling and the distance field.

**Cons**
- Ambiguous cells and coarse/fine transitions need care.
- Small enclosed features can be missed without conservative refinement.
- Still polyline output; accuracy is bounded by the distance field and cell size.

### 4. Voronoi / medial-axis offsetting

Build the Voronoi diagram of the profile's lines and arcs and trace the offset
from it.

**Pros**
- Exact and general; handles arcs.

**Cons**
- Considerable complexity for inputs of a few dozen segments.
- Harder to maintain and to integrate with the existing geometry types.

### 5. Adaptive leaf size within the current method

Stop subdividing where a single line is nearest across the whole cell.

**Pros**
- Fewer samples on straight edges.

**Cons**
- Uneven point spacing breaks greedy ordering and RDP assumptions.
- Needs endpoint handling where the nearest feature changes.

## Comparison

| Approach | Keeps arcs | Any profile | Connected output | Exactness | Added complexity |
| --- | --- | --- | --- | --- | --- |
| Current quadtree | No | Yes | No | Approximate | Existing |
| Upper envelope | Yes | No (no reversals in Z) | Yes | Exact | Low |
| Raw offset + filter | Yes | Yes | Yes | Exact if joins are correct | Medium |
| Marching squares | No | Yes | Yes | Approximate | Medium |
| Voronoi / medial axis | Yes | Yes | Yes | Exact | High |
