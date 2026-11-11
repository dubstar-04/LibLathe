Internal boring (proof of concept)
==================================

``liblathe.op.bore.BoreOP`` provides experimental internal clearing and finishing.
It is an architecture experiment; TurningAddon exposes it as
``Turn Bore`` using automatic internal model extraction and containment-based
region selection, without Base Geometry selection.
It does not generate drilling or threading.

Scope and responsibilities
--------------------------

No pilot-hole dimensions or predrilling information are required. The operation
does **not** check whether a prepared opening exists, whether the tool fits,
or whether entry/escape travel clears starting stock. Opening preparation,
insert/bar/holder fit and machine suitability are entirely the user's
responsibility. Do not treat successful generation as machining clearance
approval. Remaining-stock guidance is not involved in planning or certification.
The advisory preview can subtract emitted bore feeds using the shared stock
engine, including both clearing directions and subsequent operations. It does
not infer an existing opening; TurningAddon's initial envelope fills such
openings. See :doc:`../remaining_stock` for stock representation and limits.

The insert footprint is used to calculate cutting compensation and certify
the cutting strokes against a constructed target material region. This is
not a bar/holder model or an access check.

Input
-----

Supply only the target **inner contour**, ordered from the mouth in decreasing Z.
Do not supply an external part profile or close the bore to an outer diameter.
For Near-side tools, X is non-negative radius:

- Through bore: ``[(10, 0), (10, -20)]``.
- Blind bore including its floor: ``[(10, 0), (10, -20), (0, -20)]``.
- A wall without a terminal floor has no modelled floor to finish or protect.

Profiles must be connected and have straight first and last edges. The first
edge must progress axially into the bore. A terminal radial floor must point
toward the axis. Interior lines, tapers, steps and arcs use the existing
defeature/offset pipeline; this is not support for arbitrary bore topology or
an internal-grooving strategy. The native contour extractor's existing
accuracy and coverage limitations still apply.

Supply the insert in its actual physical orientation. A simple outward-facing
insert with its cutting corner at the origin can use
``[(-2, 0), (0, 0), (0, 2), (-2, 2)]``. Other datum positions are compensated
using the full footprint. Far-side geometry and output are reflected by the
existing ``BaseOP`` dispatch, not interpreted as a different kind of bore.

``add_containment`` sets **tool-reference** X/Z cutting limits. It does not
describe an existing opening. Cutting paths and added feed moves stay within
these limits; rapid positioning/return can leave them to reach clearance.

Parameters
----------

- ``cut_direction``: ``CutDirection.RADIAL`` (default) clears radially outward at successive
  depths toward ZMin; ``CutDirection.AXIAL`` clears toward ZMin at successively increasing
  radii. Import ``CutDirection`` from ``liblathe.op.base``. Raw strings are rejected;
  FreeCAD converts its persisted Radial/Axial text to the enum at the addon boundary.
- ``finish_passes``: number of finishing contours after clearing. Zero generates
  clearing only, to the final allowance.
- ``pass_offset``: positive maximum axial spacing for X clearing or radial
  spacing for Z clearing; also the normal spacing between finishing contours.
  This is reference-path spacing, not a maximum insert-engagement guarantee.
- ``stock_to_leave``: non-negative final normal allowance.
- ``clearance``: positive reference-space entry/escape spacing, **not certified
  stock or assembly clearance**.
- ``hfeed``: feed rate for cuts and entry/escape moves.

Clearing stops at the outermost finishing allowance (or ``stock_to_leave``
when finishing is disabled). For N finishing contours, allowances decrease from
``stock_to_leave + (N - 1) * pass_offset`` to ``stock_to_leave``. Material left
inside a bore reduces its finished radius. A blind floor's allowance moves
its cut toward the mouth. Each contour includes the existing-style 0.01
model-unit offset margin; the sampled polyline tolerance is 0.05 model units.

Geometry and routing
--------------------

The operation reflects X about a finite computational reference radius:
``u = reference_radius - x``. Tool-relative radial offsets are negated.
This maps exterior bore material into the axis-closed region expected by
the existing native defeature and positive-offset routines. The reference
radius encloses the geometry and radial containment plus padding, not the
physical stock boundary.
Terminal straight edges are extended before extraction to keep artificial
endpoint caps away from the requested cutting range. Results are reflected
back and finishing is trimmed to the selected contour's axial endpoints before containment
is applied. These axial planes are translated to the tool reference using the
insert's minimum Z: the insert's deepest point cannot pass the selected bottom.
A terminal radial floor is also trimmed at its selected inner radius, adjusted
by the insert's maximum X. Wider containment cannot turn the temporary
extensions into model-finishing strokes. Entry and escape travel remain separate.
Cutting strokes are checked against the constructed target material region.
Clearing intersects axis-aligned scan lines with the compensated allowance
boundary, retaining only the first accessible interval from the inner radius
or the mouth. It does not join disconnected regions across target material.
X clearing starts exactly at containment ZMax (Start Depth), then steps toward
the protected bottom with at most ``pass_offset`` between stations. In the
region ahead of the model mouth, it continues the compensated mouth radius;
it does not expose artificial extraction caps or extend the finished wall.
Z clearing progresses
from the inner radius outward, excluding a cut directly on the inner access
lane because it would have no inward disengagement room.
Finishing contours are reversed after clipping
so they cut the floor outward (+X), then follow the wall toward the mouth (+Z).
All cutting and added entry/withdrawal feeds are certified against the constructed
target material. No native geometry changes are required.

This reuses cutting geometry but deliberately does **not** reuse external
stock-clearance routing. Front clearance is exactly containment ZMax plus
``clearance``, with the initial destination at containment XMin (normally X=0).
For Z clearing, the tool positions to the next X radius at that front clearance,
rapids axially to containment ZMax, then feeds axially to the cutting stroke
and toward the bottom. No outward radial positioning feed is added inside the
bore for Z clearing.
X clearing and finishing enter at the inner reference radius, feeding down to
the stroke depth before feeding outward. X clearing cuts start at containment
XMin; finishing follows the contour toward the mouth. After outward radial cuts, withdrawal
first lifts in +Z by up to the smaller of ``clearance`` and ``pass_offset``,
shortened to the containment boundary, before feeding inward to XMin. At the
front boundary, where no contained lift is possible, an axial rapid reaches
front clearance before the inward rapid. Axial cuts disengage inward in X
before the axial rapid return. Thus the tool does not immediately reverse along
the surface it just cut. All added transfers are checked against the target
material; all feeds remain contained.
If the exact clearance route intersects target material, generation fails rather
than silently extending clearance past the selected limits. None of these moves
is approved against starting stock or tool-fit requirements.

Example and tests
-----------------

After building LibLathe normally:

.. code-block:: sh

   python examples/ex7_bore_op.py --direction X --no-show --output /existing/directory
   python -m pytest tests/op/test_bore_op.py -q

Choose ``--direction Z`` for axial clearing. The example writes
``bore_toolpath.png`` using the existing plotter and
``bore.gcode``. Omit ``--no-show`` for the geometry debug view.
Tests check analytic wall/floor allowances, pass order, containment, curved
geometry, reference translation, near/far reflection, routing shape and
failure without stale output.
