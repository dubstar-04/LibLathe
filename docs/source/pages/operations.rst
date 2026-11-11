Lathe Operations
================

The current operation modules provide facing, roughing, profiling, grooving
and parting, plus experimental internal clearing/finishing ``BoreOP`` and
straight centreline ``DrillOP``.
Grooving is external and radial only. Chamfering
and threading are not separate supported operation classes. In
particular, selecting the Far tool side does not enable internal boring.

.. toctree::
   :maxdepth: 1

   operations/face
   operations/rough
   operations/profile
   operations/groove
   operations/partoff
   operations/bore
   operations/drill

Insert-based operations inherit the signed-side dispatch in ``BaseOP.getGCode()``.
Supply matching physical tool, stock and part geometry; Far-side inputs and
outputs use negative X. See :doc:`liblathe_tooling` for the side enum,
reflection rules and machining limitations.
Centreline drilling shares the base generation lifecycle but uses a symmetric
drill at X=0, without insert-side dispatch.

Generation and parameters
-------------------------

Generation replaces published paths; failed validation or routing clears both
``tool_paths`` and ``clearing_paths``. Facing also builds its passes locally so a
failed later pass cannot expose a partial result.

Operations validate finite containment and clearance, positive finite cutting
increments and non-negative finite allowances where used. Finishing counts must
be non-negative integers where used. Unused settings retain their existing
meaning: parting, for example, ignores ``pass_offset``. Feed rates are passed
through unchanged. Bore and drill retain their stricter positive-clearance
requirements.

``setParams`` accepts the parameters reported by ``getParams`` plus the existing
``leadin_angle`` and ``leadout_angle`` settings. It rejects unsupported names
before applying any changes; methods and internal path state are not parameters.
Fixed-increment facing and roughing grids reject steps lost to coordinate
rounding rather than repeating the same station indefinitely.

Containment and clearance
-------------------------

Containment is a rectangle for the programmed **tool reference**, not the whole
insert footprint or the physical stock. Every feed move (G1/G2/G3), including
entry, lead-in, lead-out and withdrawal, stays inside it. Only rapid moves may
leave containment to reach clearance.

Profile, roughing and grooving extend the native contact-space defeature scan
to cover the reference-space lower Z limit, including a two-sample (0.02 mm)
margin. This does not enlarge cutting containment or change the native API;
the generated passes still use their operation's cutting limits.

External operations require a stock-clear route between clearance and the
containment boundary. Set the physical stock separately with ``add_stock(bounds)``;
without it the model's bounding box is used. If a valid boundary entry or exit
cannot be found, generation fails without publishing a partial path. Enlarge
containment to include a stock-clear entry and withdrawal rather than replacing
a stock-crossing feed with a rapid.

Grooving can use a prepared radial envelope within the selected Z range, with
the complete insert kept clear of the model. This is not a rest-stock simulation.
Boring has the same feed-containment rule but deliberately does not certify
opening, bar/holder fit or access; see :doc:`operations/bore`.

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
Near/Far dispatch and internal boring share this native transformation.
The read-only ``defeatureResolution`` and ``offsetTolerance`` class attributes
expose the native sampling and contour tolerances to Python.

If a tool origin's X coordinate is too large for the radial scan step to change
it in floating point, defeaturing raises a coordinate-precision error. The step
is not enlarged, because a coarser scan could skip thin features.
