Profiling
=========

``liblathe.op.profile.ProfileOP``

Profile follows the tool-accessible part contour. The final pass is offset from
the target by ``stock_to_leave``; additional passes are offset further out and
are cut first.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Directions
----------

* ``ProfileDirection.NEGATIVE_Z`` and ``POSITIVE_Z`` traverse each clipped
  contour in the selected axial direction.
* ``ProfileDirection.RADIAL`` splits contours at gaps and radial reversals and
  orients each run toward its floor. In Internal mode it traverses each
  connected bore contour from the bottom toward the mouth, retracing the ``-Z``
  pass and its leads so each pass exits axially through the mouth. With
  ``allow_grooving`` in External mode, passes reposition at the same local
  lane as Rough grooving (containment upper radius plus clearance); only
  operation entry and final return use the global stock/model clearance.

Parameters
----------

- ``direction``: a ``ProfileDirection`` member; defaults to ``NEGATIVE_Z``.
- ``mode``: ``MachiningMode.EXTERNAL`` or ``MachiningMode.INTERNAL``.
- ``finish_passes``: number of profile offsets (no intermediate passes are
  added).
- ``pass_offset``: normal spacing between profile offsets.
- ``stock_to_leave``: material left on the finished profile.
- ``allow_grooving``: permit the profile to follow tool-accessible grooves.
- ``clearance``: distance used by rapid routing.
- ``hfeed``: feed rate.

Internal mode maps selected inner-profile radii into the shared external
planning frame, reflects the tool-relative X coordinates, then maps paths back
to physical X. Near/Far reflection is applied independently. Internal access
uses the axis-side containment boundary; selected-profile and protected-feed
checks do not certify a pre-existing opening or bar/holder fit.

Each offset is clipped to tool-reference containment before routing; excluded
regions split it into strokes and offsets outside containment are omitted.
Protected approaches and withdrawals are checked against the part. Feed moves
stay inside containment. External rapid transfers may cross the physical stock
envelope outside containment; assess remaining stock before machining. With
physical stock supplied through ``add_stock(bounds)``, its envelope is used for
external clearance positioning.
