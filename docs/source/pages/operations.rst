Lathe Operations
================

The operation modules provide ``RoughOP`` and ``ProfileOP`` strategies for
external and internal turning, plus parting, straight centreline drilling and
threading. Facing is Rough in the Radial direction; groove roughing and finishing
are separate Rough and Profile operations. Threading currently supports
straight, single-start threads with radial infeed. Chamfering is not a separate
operation.

.. toctree::
   :maxdepth: 1

   operations/rough
   operations/profile
   operations/partoff
   operations/drill
   operations/thread

Insert-based operations inherit the signed-side dispatch in ``BaseOP.getGCode()``.
Supply matching physical tool, stock and part geometry; Far-side inputs and
outputs use negative X. See :doc:`liblathe_tooling` for the side enum,
reflection rules and machining limitations.
Centreline drilling shares the base generation lifecycle but uses a symmetric
drill at X=0, without insert-side dispatch.
Rough and Profile additionally expose ``MachiningMode.EXTERNAL`` and
``MachiningMode.INTERNAL``. Internal mode transforms selected internal profile
geometry into the shared external planning frame and reflects the resulting
paths back into physical X coordinates; it is independent of Near/Far tool
side. Internal access enters from the axis side and is checked against the
selected contour, but does not certify a pre-existing opening, bar/holder fit
or machine clearance.

Generation and parameters
-------------------------

Generation replaces published paths; failed validation or routing clears both
``tool_paths`` and ``clearing_paths``.

Operations validate finite containment and clearance, positive finite cutting
increments and non-negative finite allowances where used. Finishing counts must
be non-negative integers where used. Unused settings retain their existing
meaning: parting, for example, ignores ``pass_offset``. Feed rates are passed
through unchanged. Drill retains its stricter positive-clearance requirement.
Threading also requires positive clearance and uses pitch rather than F-word
feeds; its supported parameters are listed in :doc:`operations/thread`.

``setParams`` accepts the parameters reported by ``getParams`` plus the existing
``leadin_angle`` and ``leadout_angle`` settings. It rejects unsupported names
before applying any changes; methods and internal path state are not parameters.
Fixed-increment roughing grids reject steps lost to coordinate
rounding rather than repeating the same station indefinitely.

Containment and clearance
-------------------------

Containment is a rectangle for the programmed **tool reference**, not the whole
insert footprint or the physical stock. Every feed move (G1/G2/G3/G33), including
entry, lead-in, lead-out and withdrawal, stays inside it. Only rapid moves may
leave containment to reach clearance.

Profile and roughing extend the native contact-space defeature scan
to cover the reference-space lower Z limit, including a two-sample (0.02 mm)
margin. This does not enlarge cutting containment or change the native API;
the generated passes still use their operation's cutting limits.

External operations rapid to and from the tool-reference containment boundary,
even when it lies inside the original stock. Users must evaluate these transfers
against remaining stock before machining; the remaining-stock preview is advisory,
not automatic route approval. Set physical stock with ``add_stock(bounds)`` to
choose initial clearance outside its envelope; otherwise model bounds are used.
Protected routes retain full-insert checks against the finished part. If no valid
entry or withdrawal exists, generation fails without publishing a partial path.

In Rough, Radial steps along -Z through the whole containment, cutting one full
radial stroke into the material at each station. It also represents facing and
groove roughing. Use ``allow_grooving`` when the tool is intended to enter
grooves; enabled Radial strokes retract radially through the plunge before moving
axially at the containment-based local clearance. Operation entry and final
return retain global stock/model clearance. The local lane must be prepared;
it is checked against the finished part, not automatically approved against
remaining stock. Profile's Radial direction splits disconnected and reversing contours
so cuts proceed toward each groove floor, using the same local lane when
``allow_grooving`` is enabled; it also finishes internal profiles
from the bottom toward the mouth, exiting axially through the mouth like a
reversed ``-Z`` pass.

Performance and Safety
----------------------

Defeaturing reuses prepared boundary boxes and containment tolerances. During
radial scanning, a contained vertex's conservative distance to the boundary
identifies positions that must still collide, avoiding repeated collision
queries within that span. The original floating-point scan grid is preserved;
collision is not assumed to be monotone.

Prepared boundary queries prune straight edges using their existing bounds.
Nearest-point queries skip a line only when its box cannot improve the current
distance; ray classification skips lines outside the query's X range or wholly
below it. Remaining candidates use the same exact calculations. Arc queries,
boundary inclusion, scan spacing and clearance tolerances are unchanged.

Positions near the boundary still undergo the full insert checks. Connector
and chord sweeps, clearance tolerances and subdivision limits are unchanged.
Uncertifiable paths continue to raise an error rather than emitting unchecked
moves.

``SegmentGroup.validateToolSweeps(tool, moves)`` validates an ordered sequence
of ``(start, end)`` points using one native snapshot of the part and tool.
It uses the same checks as individual ``validateToolSweep`` calls, stops at
the first failure and reports its zero-based move index and coordinates.
An empty sequence is a no-op. Snapshots are rebuilt on every call, so subsequent
geometry edits are observed. Python calls retain the GIL.

``SegmentGroup.reflectX(radius=0)`` returns an independent contour mapped by
``X = radius - X``, with arc bulges reflected and traversal order retained.
Near/Far dispatch and Internal mode share this native transformation.
The read-only ``defeatureResolution`` and ``offsetTolerance`` class attributes
expose the native sampling and contour tolerances to Python.

If a tool origin's X coordinate is too large for the radial scan step to change
it in floating point, defeaturing raises a coordinate-precision error. The step
is not enlarged, because a coarser scan could skip thin features.
