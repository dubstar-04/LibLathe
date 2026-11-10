Roughing
========

``liblathe.op.rough.RoughOP``

.. figure:: /LL_static/images/RoughingOp.jpeg
    :align: center
    :figwidth: 450px

Roughing removes the bulk of the material between the stock and the part.
Each pass runs axially along Z at a fixed radius and stops where it meets the
part, with lead-in and lead-out moves where a pass starts or ends on the part.

Passes are spaced by ``pass_offset`` in X and are cut from the outside of the
containment inwards. The part is first defeatured for the tool, so areas the tool
cannot reach are left uncut.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``pass_offset`` (Radial Pass Offset): radial distance between roughing
  passes (radius, not diameter).
- ``stock_to_leave``: material left on the part for later operations.
- ``allow_grooving``: allow passes to enter grooves and undercuts the tool can
  reach.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Approach and retract moves are checked against the part.

Containment bounds the programmed tool-reference path, not the insert footprint.
It is independent of physical stock and may extend beyond it to provide room for
lead-in and lead-out moves.
Lead-in and lead-out moves are shortened along their original direction to fit
these limits, omitted when no room remains, and checked with a full-insert sweep
against the part. Feed approaches also stay inside containment.
Approaches follow the first cutting or lead-in direction where safe.
Rapid approaches use separate X and Z moves, positioning radially at axial
clearance before approaching in Z where safe.
After the lead-out, the tool feeds radially outward to stock plus clearance,
even when this lies outside containment. It then returns at rapid speed; it never
reverses along the last cut. Withdrawals are checked against the full part and
rapid transfers against both stock and part. Set physical stock with ``add_stock(bounds)``.
If omitted, the containment box is used as a conservative stock envelope.
If no safe entry or radial withdrawal exists, generation fails explicitly.
