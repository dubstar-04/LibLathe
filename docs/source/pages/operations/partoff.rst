Parting
=======

``liblathe.op.partoff.PartoffOP``

.. figure:: /LL_static/images/PartingOp.jpeg
    :align: center
    :figwidth: 450px

Parting cuts the finished part off the stock. It is a single radial pass from
outside containment down to its minimum X, positioned just beyond its minimum Z.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Set the containment's minimum X to zero to part the component off completely.
