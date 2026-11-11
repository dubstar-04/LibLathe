Lathe Operations
================

The current operation modules provide facing, roughing, profiling, grooving
and parting, plus an experimental internal clearing/finishing ``BoreOP``.
Grooving is external and radial only. Chamfering,
threading and drilling are not separate supported operation classes. In
particular, selecting the Far tool side does not enable internal boring.

.. toctree::
   :maxdepth: 1

   operations/face
   operations/rough
   operations/profile
   operations/groove
   operations/partoff
   operations/bore

All operations inherit the signed-side dispatch in ``BaseOP.getGCode()``.
Supply matching physical tool, stock and part geometry; Far-side inputs and
outputs use negative X. See :doc:`liblathe_tooling` for the side enum,
reflection rules and machining limitations.

Containment and clearance
-------------------------

Containment is a rectangle for the programmed **tool reference**, not the whole
insert footprint or the physical stock. Every feed move (G1/G2/G3), including
entry, lead-in, lead-out and withdrawal, stays inside it. Only rapid moves may
leave containment to reach clearance.

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

Positions near the boundary still undergo the full insert checks. Connector
and chord sweeps, clearance tolerances and subdivision limits are unchanged.
Uncertifiable paths continue to raise an error rather than emitting unchecked
moves.

If a tool origin's X coordinate is too large for the radial scan step to change
it in floating point, defeaturing raises a coordinate-precision error. The step
is not enlarged, because a coarser scan could skip thin features.
