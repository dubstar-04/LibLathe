Facing
======

``liblathe.op.face.FaceOP``

.. figure:: /LL_static/images/FacingOp.jpeg
    :align: center
    :figwidth: 450px

Facing machines the end of the stock down to the end of the part. Each pass
cuts radially across the face, from containment's maximum X to its minimum
X, followed by a short lead-out clipped to containment.

Passes are spaced by ``pass_offset`` along Z, from the end of the part plus
``stock_to_leave`` up to the containment's maximum Z, and are cut starting
from that limit.
No pass extends below containment's minimum Z. All entry and withdrawal feeds
also stay inside containment. Rapids connect its boundary to clearance, including
through the original stock envelope. Users must assess remaining stock before
machining. Set physical stock separately with ``add_stock(bounds)`` for initial
clearance positioning.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``pass_offset`` (Axial Pass Offset): axial distance between facing passes.
- ``stock_to_leave``: material left on the face of the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Facing passes are stored in ``clearing_paths``.
