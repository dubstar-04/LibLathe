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
stock inwards. The part is first defeatured for the tool, so areas the tool
cannot reach are left uncut.

Parameters
----------

- ``pass_offset``: radial depth of each roughing pass.
- ``stock_to_leave``: material left on the part for later operations.
- ``allow_grooving``: allow passes to enter grooves and undercuts the tool can
  reach.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Approach and retract moves are checked against the part.
