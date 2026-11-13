Roughing
========

``liblathe.op.rough.RoughOP``

Rough removes material between the prepared stock and the target profile.
Direction selects the pass axis:

* ``RoughDirection.NEGATIVE_Z`` and ``POSITIVE_Z`` make axial passes at
  successive X stations.
* ``RoughDirection.RADIAL`` steps along -Z, cutting one full radial stroke
  into the material at each station: toward the axis externally, toward the
  bore wall internally. Station spacing is capped by the tool width,
  and extra stations are added at faces and against both groove walls.

The Radial strategy is also used for facing and groove roughing; enable
``allow_grooving`` when the tool is intended to enter grooves and undercuts.
With grooving enabled, every stroke withdraws straight radially at the same Z,
back through its plunge. There is no sideways or diagonal pull-off inside the
groove. External passes reposition at containment's upper radius plus clearance,
adjusted for an insert extending inward from its reference. Only operation
entry and final return use the global stock/model clearance. The local lane
must already be clear of material; finished-part sweep checks reject blocked
routes rather than silently switching to global clearance.

Without grooving enabled, facing strokes retain a +Z pull-off using the lead-out
angle and ``pass_offset`` length, shortened to fit containment and clear the part.
If no pull-off fits, generation fails. The first facing station sits below the
upper Z limit by the pull-off rise.

Rough and Profile remain separate operations, so Rough can leave a finishing
allowance without coupling roughing to the number or spacing of finish passes.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``direction``: a ``RoughDirection`` member; defaults to ``NEGATIVE_Z``.
- ``mode``: ``MachiningMode.EXTERNAL`` or ``MachiningMode.INTERNAL``.
- ``pass_offset``: axial spacing between Radial strokes; for axial directions it is
  the radial spacing between passes.
- ``stock_to_leave``: material left for a later Profile operation.
- ``allow_grooving``: permit the tool-accessible profile to enter grooves.
- ``clearance``: distance used by rapid routing.
- ``hfeed``: feed rate.

Internal mode maps selected inner-profile radii into the shared external
planning frame, reflects the tool-relative X coordinates, then maps paths back
to physical X. Near/Far reflection is applied independently. Internal Radial
roughing cuts from the axis side toward the bore wall. The selected contour and
protected feed routes are checked, but the operation does not certify a
pre-existing opening or bar/holder fit.

Protected approaches and withdrawals are checked against the part. Feed moves
stay inside tool-reference containment. External rapid transfers may cross the
physical stock envelope outside containment; assess remaining stock before
machining. With physical stock supplied through ``add_stock(bounds)``, its
envelope is used for global clearance positioning.
