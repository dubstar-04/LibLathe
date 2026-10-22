# Architecture: profile offsetting

This document records how LibLathe offsets profiles today, the alternatives
considered, and the trade-offs of each. It is a decision aid, not a commitment:
the pros and cons are reasoned from the code and a small number of measurements,
and should be validated with benchmarks before any change.
See [PLAN.md](PLAN.md) for the correctness and performance work in progress.

## Problem

Part profiles are open chains of lines and arcs in X (radius) and Z (axis),
starting at X = 0. Operations need:

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
   - Evaluate a signed distance field (distance to the nearest segment, sign from
     a ray-crossing test against the profile closed along the axis).
   - Subdivide a quadtree where `|distance - offset|` is within the cell's
     half-diagonal, down to 0.2 cell width.
   - Project each leaf centre onto the nearest profile point and push it out by
     the offset.
   - Order the points by greedy nearest neighbour, then simplify with
     Ramer-Douglas-Peucker (tolerance 0.01).

On the example part this measured about 550 points with a distance error of at
most 0.005, no dropped points and consecutive spacing of about 0.15.

**Pros**
- Topology is handled implicitly: corners, concave regions, small loops and
  negative offsets need no trimming logic.
- One method serves any offset distance and sign.
- Projection gives sub-cell accuracy.

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
