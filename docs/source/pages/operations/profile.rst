Profiling
=========

``liblathe.op.profile.ProfileOP``

.. figure:: /LL_static/images/ProfilingOp.jpeg
    :align: center
    :figwidth: 450px

Profiling follows the shape of the part to produce the finished surface. Each
pass is an offset of the part profile, started with a lead-in from the end of
the containment.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

The final pass is offset from the part by ``stock_to_leave``. Additional passes
are offset further out by ``pass_offset`` and are cut first, finishing on the
pass closest to the part.

Parameters
----------

- ``finish_passes``: number of profile passes.
- ``pass_offset`` (Pass Offset): normal distance between successive profile passes.
- ``stock_to_leave``: material left on the part.
- ``allow_grooving``: allow the profile to follow grooves and undercuts the
  tool can reach.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Approach and retract moves are checked against the part.
