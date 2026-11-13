External threading
==================

``liblathe.op.thread.ThreadOP`` generates straight, single-start external
threads using explicit spindle-synchronized ``G33`` passes. Infeed is radial, from the
crest towards the root; every pass traverses the same ZMax-to-ZMin stroke.
Tapered threads, multi-start threads, compound infeed and ``G76`` cycles are
not implemented.

Dimensions and tool datum
-------------------------

Use the existing tool-reference containment interface:

* XMax is the crest reference radius and XMin is the final root reference radius.
  Both must be positive in the Near planning frame, with XMin strictly below XMax.
* ZMax is the synchronized start and ZMin is the synchronized end.
* With a tool-tip datum at (0, 0), set XMax to major diameter / 2 and XMin to
  minor diameter / 2. For another datum, translate the limits to that reference.
  LibLathe does not relocate the supplied tool origin or apply nose compensation.

Choose the minor diameter and actual insert geometry for the required thread
form and tolerances. No ISO/Unified profile dimensions are inferred from pitch.
Supply the insert in its physical pose. Signed Near/Far inputs and outputs
follow the same conventions as the other insert operations.

Parameters
----------

``getParams`` / ``setParams`` expose:

* ``pitch``: required, finite positive distance per revolution, in the active
  length units. For this single-start operation, pitch and lead are equal.
* ``pass_offset``: positive radial infeed per pass; default 0.1 model units.
  The final increment is shortened to land exactly at the root radius.
* ``spring_passes``: non-negative integer number of additional full-depth
  passes; default 0.
* ``clearance``: positive radial/axial clearance; default 3 model units.

There is no F-word feed for threading: ``G33 K<pitch>`` controls synchronization.
``hfeed``, ``vfeed``, ``finish_passes``, ``stock_to_leave`` and ``cut_direction``
are not threading parameters. Each cutting pass is also published as its own
straight ``tool_paths`` group; failed generation clears the published paths.

Entry, withdrawal and clearance
-------------------------------

The blank must already be prepared to the desired crest size. The synchronized
stroke must include suitable run-in and run-out space, outside material or in
prepared reliefs. No run-in allowance, exit taper or pull-out helix is added.
In particular, do not end a pass against a shoulder and expect a synchronized
radial withdrawal.

At each pass, the tool rapids radially to depth at ZMax, synchronizes and cuts
to ZMin, then rapids radially to a local clearance lane: the containment crest
(XMax) plus the insert's extent below its tip plus ``clearance``. It returns
axially along that lane, which is checked against the unthreaded part, to the
next pass. The blank above the containment must therefore already be turned.
The deepest radial entry is checked with the full insert against the supplied
unthreaded part, so ZMax must leave run-in space clear of material. The deepest
pass and its radial withdrawal are checked against the part with the thread band
(radius at or above the root, between ZMin and ZMax) removed, because the passes
cut that material; anything outside the band, such as a shoulder without a
run-out relief beyond ZMin, still fails generation. A missing or uncertifiable
clearance route fails generation. The thread band is not treated as a protected
final thread surface.

The initial approach and final return use a clearance corner that includes the
insert bounds and the physical stock envelope when supplied, otherwise model
bounds. As with other
external operations, original-stock access and remaining-stock preparation
remain the user's responsibility. Checks do not certify holders, fixtures,
machine travel or the first move from an unknown machine position.

Machine setup
-------------

Output explicitly selects ``G18`` (XZ), ``G90`` (absolute) and ``G8`` (radius
mode); these modes remain active afterwards. The caller selects units, work and
tool offsets, spindle direction and a suitable fixed RPM (``G97 S... M3/M4``),
with controller cutter/nose compensation disabled (``G40``).
Do not pass the resulting X radii through a diameter conversion while retaining
``G8``. No spindle, tool-change or program-end commands are added by the operation.

The operation uses the controller's default spindle. Configure its encoder/index
and at-speed signals for synchronized motion. Every pass uses the same start Z and
waits for spindle synchronization;
thread hand depends on the spindle direction and the negative-Z cutting direction.
The caller must validate spindle speed, axis velocity/acceleration and the actual
machine setup. An offline interpreter check cannot verify these.

Example
-------

This example uses millimetres, a tip datum, a 20 mm crest diameter and an
explicit 18.5 mm root diameter. These are illustrative dimensions, not a
standard thread specification.

.. code-block:: python

   import math
   from liblathe.base.point import Point
   from liblathe.base.segment import Segment
   from liblathe.op.thread import ThreadOP
   from liblathe.tool.tool import Tool

   tool = Tool()
   vertices = [Point(0, 0), Point(2, -2 / math.sqrt(3)),
               Point(2, 2 / math.sqrt(3)), Point(0, 0)]
   tool.set_tool_from_segments([Segment(a, b) for a, b in zip(vertices, vertices[1:])])
   operation = ThreadOP()
   operation.add_tool(tool)
   part = [Point(0, 0), Point(10, 0), Point(10, -20), Point(0, -20)]
   operation.addPartSegments([Segment(a, b) for a, b in zip(part, part[1:])])
   operation.add_containment_from_limits(18.5 / 2, 20 / 2, -22, 2)
   operation.setParams({"pitch": 1.5, "pass_offset": 0.1,
                        "spring_passes": 1, "clearance": 2})
   for command in operation.getGCode():
       print(command.to_string())

Wrap the output in a machine-appropriate program with units, offsets, spindle
setup and program end. ``Plot.backplot`` can display the G33 passes as XZ
projections, not helical thread geometry. The axisymmetric ``StockPreview``
cannot represent threads: do not subtract G33 passes as revolved cutting feeds.
There is no threading integration in TurningAddon or FreeCAD_Path_Sim yet.

Tests
-----

.. code-block:: sh

   python -m pytest tests/op/test_thread_op.py tests/gcode/test_command.py -q
