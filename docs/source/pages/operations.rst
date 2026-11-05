Lathe Operations
================

The current operation modules provide roughing, facing, profiling and parting.
Grooving, boring, chamfering, threading and drilling are not separate supported
operation classes. In particular, selecting the Far tool side does not enable
internal boring.

All operations inherit the signed-side dispatch in ``BaseOP.getGCode()``.
Supply matching physical tool, stock and part geometry; Far-side inputs and
outputs use negative X. See :doc:`liblathe_tooling` for the side enum,
reflection rules and machining limitations.

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


