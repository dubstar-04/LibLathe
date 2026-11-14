Centreline drilling (proof of concept)
========================================

``liblathe.op.drill.DrillOP`` drills at X=0 in decreasing Z, either in one feed
or in fixed-depth pecks. It needs no target contour and uses explicit G0/G1
commands, not controller-specific canned cycles. Tapping, off-axis/live-tool
drilling and automatic hole recognition remain outside this POC.

Tool and depths
---------------

``liblathe.tool.drill.Drill(diameter, tip_angle=118, length=50)`` describes an
ideal pointed cylindrical drill. Dimensions are millimetres and the included
point angle is in degrees, strictly between 0 and 180. The datum is the drill
tip at (0, 0), with the body extending in positive Z. The full symmetric XZ
outline is a convex pentagon. Its point length is
``diameter / (2 * tan(tip_angle / 2))`` with the angle converted to radians.

Final depth means **tip depth** by default. With ``tip_compensation=True``,
it instead specifies the full-diameter hole depth: the tip travels one calculated
point length farther in negative Z. The reach check includes this extension.
There is no automatic breakthrough allowance or target-model protection.

The axial stroke must not exceed the tool's ``length``. This is only an
overall reach check, not a flute-length, chuck, holder or assembly check.
There is no Front/Rear choice and no insert compensation or orientation
selection. A rotated drill is rejected. Spindle settings belong to the caller.

Routing and stock
-----------------

Containment must include X=0 and have a positive axial extent. Its ZMax is
start depth and ZMin is the requested final depth. Tip compensation deliberately
extends the feed beyond ZMin.
By default, the operation rapids to X=0 at ``start + clearance``, approaches the start
depth axially at rapid, feeds once to final depth at ``vfeed`` and retracts
axially to front clearance at rapid. Clearance must be positive. Feed is passed
through unchanged, consistently with the other turning operations; configuring
a suitable machining feed remains the caller's responsibility.

Pecking
-------

``peck_depth=0`` preserves the single-feed behaviour. A positive value sets the
maximum new axial depth per peck; the final peck is shortened to end exactly at
the final tip position, including compensation when enabled.

``retract_mode`` selects a ``RetractMode`` enumeration member:

* ``RetractMode.FULL_RETRACT`` returns to ``start + clearance`` after every peck.
  Rapid re-entry stops ``reentry_gap_diameters * drill.diameter`` above the
  previous peck depth, capped at Start Depth. Feeding resumes from there.
* ``RetractMode.PARTIAL_RETRACT`` retracts by
  ``chip_break_retract_diameters * drill.diameter`` between pecks, also capped
  at Start Depth, then feeds to the next depth. Only the final retract returns
  to front clearance.

Both diameter multipliers default to ``1.0`` and must be finite and positive
when their mode is active. A gap larger than the preceding peck can cause
re-feeding from Start Depth. The rapid optimizer preserves drilling reversals
and nonzero partial retracts.

Path coordinates use native single precision. Compensation, peck advances and
retracts that vanish at that precision are rejected. The reach check includes
the stored final depth, and an operation is limited to 10,000 pecks.

Start depth is the user-defined entry plane, even when it lies inside the
original stock envelope. No starting-stock access check is performed and the
entry plane is not automatically moved to the stock front. The initial move
from an unknown machine position is not certified. The
user remains responsible for entry, retract suitability, chip evacuation,
tool reach, spindle direction and all machine/fixture clearances.

The same native ``StockPreview`` can subtract the drill's generated feed sweep,
including its conical point. Neither peck retractions nor rapid moves should
be subtracted. This preview is advisory and does not approve internal machining
access or become planner input. See :doc:`../remaining_stock`.

Example
-------

.. code-block:: python

   from liblathe.op.drill import DrillOP, RetractMode
   from liblathe.tool.drill import Drill

   operation = DrillOP()
   operation.add_tool(Drill(diameter=5, tip_angle=118, length=50))
   operation.add_containment_from_limits(0, 2.5, -15, 0)
   operation.vfeed = 75
   operation.clearance = 3
   operation.setParams({
       "peck_depth": 4,
       "retract_mode": RetractMode.FULL_RETRACT,
       "tip_compensation": True,
   })
   for command in operation.getGCode():
       print(command.to_string())

TurningAddon exposes this as **Turn Drill**, using a native FreeCAD
**Drill** ToolBit's Diameter, TipAngle and overall Length. Its Containment
page exposes only Start Depth and Final Depth, with X fixed at zero.
The Operation page controls peck depth, retraction mode and tip
compensation. The final-depth label changes to Full-diameter depth when
compensation is enabled; the containment guide still marks the requested
depth, not the extended tip position.
Vertical Feed supplies ``vfeed`` and the job Safe Height Offset supplies
front clearance. No Base Geometry selection is required.

Tests
-----

.. code-block:: sh

   python -m pytest tests/op/test_drill_op.py -q

Tests cover straight and pecked commands, preserved full retracts, diameter-based
gaps, tip compensation, translated depths, invalid parameters, reach checks,
user-defined entry planes inside original stock, cleared output on failure and
analytic blind/through-hole remaining stock, without changing input paths.
