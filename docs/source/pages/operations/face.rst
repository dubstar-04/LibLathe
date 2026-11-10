Facing
======

``liblathe.op.face.FaceOP``

.. figure:: /LL_static/images/FacingOp.jpeg
    :align: center
    :figwidth: 450px

Facing machines the end of the stock down to the end of the part. Each pass
cuts radially across the face, from outside containment to its minimum
X, followed by a short lead-out.

Passes are spaced by ``pass_offset`` along Z, from the end of the part plus
``stock_to_leave`` up to the containment's maximum Z, and are cut starting
from that limit.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``pass_offset`` (Axial Pass Offset): axial distance between facing passes.
- ``stock_to_leave``: material left on the face of the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Facing passes are stored in ``clearing_paths``.
