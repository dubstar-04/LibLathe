Centreline drilling (proof of concept)
========================================

``liblathe.op.drill.DrillOP`` performs one straight drilling feed at X=0 in
decreasing Z. It needs no target contour and uses explicit G0/G1 commands, not
controller-specific canned cycles. Pecking, tapping, off-axis/live-tool drilling
and automatic hole recognition are outside this POC.

Tool and depths
---------------

``liblathe.tool.drill.Drill(diameter, tip_angle=118, length=50)`` describes an
ideal pointed cylindrical drill. Dimensions are millimetres and the included
point angle is in degrees, strictly between 0 and 180. The datum is the drill
tip at (0, 0), with the body extending in positive Z. The full symmetric XZ
outline is a convex pentagon. Its point length is
``diameter / (2 * tan(tip_angle / 2))`` with the angle converted to radians.

Final depth always means **tip depth**, not the bottom of the full-diameter
hole. The full-diameter bottom is one point length ahead of the tip. Through
drilling is possible by explicitly setting a sufficiently deep tip depth;
there is no automatic breakthrough allowance or target-model protection.

The axial stroke must not exceed the tool's ``length``. This is only an
overall reach check, not a flute-length, chuck, holder or assembly check.
There is no Front/Rear choice and no insert compensation or orientation
selection. A rotated drill is rejected. Spindle settings belong to the caller.

Routing and stock
-----------------

Containment must include X=0 and have a positive axial extent. Its ZMax is
start depth and ZMin is final tip depth. All feeds remain inside containment.
The operation rapids to X=0 at ``start + clearance``, approaches the start
depth axially at rapid, feeds once to final depth at ``vfeed`` and retracts
axially to front clearance at rapid. Clearance must be positive. Feed is passed
through unchanged, consistently with the other turning operations; configuring
a suitable machining feed remains the caller's responsibility.

Start depth is the user-defined entry plane, even when it lies inside the
original stock envelope. No starting-stock access check is performed and the
entry plane is not automatically moved to the stock front. The initial move
from an unknown machine position is not certified. The
user remains responsible for entry, retract suitability, chip evacuation,
tool reach, spindle direction and all machine/fixture clearances.

The same native ``StockPreview`` can subtract the drill's generated feed sweep,
including its conical point. Neither peck retractions nor rapid moves should
be subtracted. This preview is advisory and does not become boring access
approval or planner input. See :doc:`../remaining_stock`.

Example
-------

.. code-block:: python

   from liblathe.op.drill import DrillOP
   from liblathe.tool.drill import Drill

   operation = DrillOP()
   operation.add_tool(Drill(diameter=5, tip_angle=118, length=50))
   operation.add_containment_from_limits(0, 2.5, -15, 0)
   operation.vfeed = 75
   operation.clearance = 3
   for command in operation.getGCode():
       print(command.to_string())

TurningAddon exposes this as **Turn Drill**, using a native FreeCAD
**Drill** ToolBit's Diameter, TipAngle and overall Length. Its Containment
page exposes only Start depth and Final tip depth, with X fixed at zero.
Vertical Feed supplies ``vfeed`` and the job Safe Height Offset supplies
front clearance. No Base Geometry selection is required.

Tests
-----

.. code-block:: sh

   python -m pytest tests/op/test_drill_op.py -q

Tests cover exact tip-depth commands, translated depths, invalid parameters,
reach checks, user-defined entry planes inside original stock, cleared output
on failure and analytic blind/
through-hole remaining stock, without changing input paths.
