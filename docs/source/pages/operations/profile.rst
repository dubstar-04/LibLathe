Profiling
=========

``liblathe.op.profile.ProfileOP``

.. figure:: /LL_static/images/ProfilingOp.jpeg
    :align: center
    :figwidth: 450px

Profiling follows the shape of the part to produce the finished surface. Each
pass is an offset of the part profile with bounded lead-in and lead-out moves.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

The final pass is offset from the part by ``stock_to_leave``. Additional passes
are offset further out by ``pass_offset`` and are cut first, finishing on the
pass closest to the part.

Parameters
----------

- ``finish_passes``: number of profile offsets (no intermediate passes are added).
- ``pass_offset`` (Pass Offset): fixed normal increment between profile offsets
  and fixed X increment between their axial lead-in lines.
- ``stock_to_leave``: material left on the part.
- ``allow_grooving``: allow the profile to follow grooves and undercuts the
  tool can reach.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Approach and retract moves are checked against the part.

Each offset pass is clipped to the tool-reference X/Z containment before leads
are added. Excluded regions split the contour into separate strokes; offsets
wholly outside containment are omitted.
Profile lead-ins feed axially in Z at constant X.
Profile extraction retains the SDF contour beyond the original starting Z.
Each fixed-offset contour is trimmed at its first intersection with an axial
lead-in line. These lines start at the base profile's starting X and increase
by ``pass_offset`` per contour. This retains normal contour spacing near a
rounded nose without inserting extra passes. Containment can shorten or omit
these entries and can split one offset into several strokes.
Containment remains strict: increase its starting Z to retain entries whose
intersections lie beyond the current limit. The limit must also leave room for
the desired axial lead-in length. Extending extraction does not permit feeds
outside containment.
The final ``stock_to_leave`` allowance is unchanged.
Cutting and entry feeds stay inside containment. As with roughing, withdrawals
feed radially out to stock plus clearance and may leave containment; rapid
approaches use separate X/Z moves checked against stock and part.
Set physical stock with ``add_stock(bounds)``; otherwise containment is used as
a conservative stock envelope. Unsafe entries or withdrawals fail explicitly.
