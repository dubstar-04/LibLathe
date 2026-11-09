Facing
======

``liblathe.op.face.FaceOP``

.. figure:: /LL_static/images/FacingOp.jpeg
    :align: center
    :figwidth: 450px

Facing machines the end of the stock down to the end of the part. Each pass
cuts radially across the face, from outside the stock to the stock's minimum
X, followed by a short lead-out.

Passes are spaced by ``step_over`` along Z, from the end of the part plus
``stock_to_leave`` up to the end of the stock, and are cut starting from the
end of the stock.

Parameters
----------

- ``step_over``: axial depth of each facing pass.
- ``stock_to_leave``: material left on the face of the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Facing passes are stored in ``clearing_paths``.
