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


