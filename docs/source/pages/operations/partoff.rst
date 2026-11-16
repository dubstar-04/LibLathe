Parting
=======

``liblathe.op.partoff.PartoffOP``

.. figure:: /LL_static/images/PartingOp.jpeg
    :align: center
    :figwidth: 450px

Parting cuts the finished part off the stock. It is a single radial pass from
containment's maximum X down to its minimum X.

Parting containment describes the kerf the tool cuts:

- Maximum Z is the parting face, the back face of the finished part. The tool is
  offset so its +Z edge sits on this face, whichever point the tool is referenced
  from, so the tool never crosses the face. The face must not be inside the part;
  it may be moved toward -Z to leave extra length.
- Minimum Z is the -Z side of the kerf. The containment must be at least as wide
  as the tool, normally maximum Z minus the tool width.
- The tool's reference point must lie within the tool's axial extent.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(radial_min, radial_max, axial_min, axial_max)``.

Parameters
----------

- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.
- ``peck_depth``: maximum radial depth of each peck. Zero, the default, cuts in
  one feed. Pecks are evenly spaced down to the containment's minimum X.
- ``retract_mode``: a ``liblathe.op.base.RetractMode`` used between pecks.
  ``PARTIAL_RETRACT`` backs off radially to break the chip, then feeds on.
  ``FULL_RETRACT`` (the default) rapids out to the cut's start radius to clear the
  chip, then rapids back to the re-entry gap above the last peck.
- ``chip_break_retract_widths``: the partial-retract back-off as a multiple of
  the tool width (default 1).
- ``reentry_gap_widths``: the full-retract re-entry gap as a multiple of the tool
  width (default 1).

Set the containment's minimum X to zero to part the component off completely.
Approach and withdrawal feeds also remain inside containment. The tool withdraws
radially through the kerf after the cut; axial repositioning
occurs at radial stock clearance, never as a feed through the component.
Rapids connect the containment boundary to clearance and may cross the original
stock envelope. Users must assess remaining stock before machining. Supply
physical stock with ``add_stock(bounds)`` for initial clearance positioning.
