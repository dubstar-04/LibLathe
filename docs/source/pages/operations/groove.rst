Grooving
========

``liblathe.op.groove.GrooveOP``

Grooving machines external grooves with a series of radial plunges. The containment
X and Z limits select the area to groove, so a single groove or the whole part
can be machined.

Plunges are spaced evenly along Z, slightly less than the tool's width apart,
so neighbouring plunges overlap by 10% of the tool width. Each depth layer of
``pass_offset`` is completed across every station before the next, deeper layer
begins. Plunges stop at the part or the containment's minimum X.

The tool always retracts radially out of the stock before moving to the next
Z station. After the plunges, optional finishing passes follow the groove's
walls and floor to remove the small ridges plunges leave on sloped or curved
walls. Each finishing contour is split into connected strokes at changes in
radial direction. Outward-running strokes are reversed, so both walls are cut
toward the centerline: decreasing X on the near side and increasing X on the
far side. Constant-X floor traversals are retained. The tool retracts radially
and repositions at clearance between strokes; it does not follow a wall outward
to reach the next stroke. Curved walls use the existing offset polyline.

Parameters
----------

- ``pass_offset`` (Radial Pass Offset): radial distance between plunge
  layers (radius, not diameter).
- ``finish_passes``: number of finishing contours.
  Each pass completes all inward-oriented strokes along one contour;
  ``0`` disables them. This counts complete contours, not individual strokes.
- ``finish_pass_offset`` (Finish Pass Offset): non-negative
  normal offset between finishing contours
  (default ``0``). With ``N`` passes and offset ``d``, finishing allowances
  decrease from ``stock_to_leave + (N - 1) * d`` to ``stock_to_leave``.
  Plunging stops at the first finishing contour, reserving material for the
  remaining passes. For example, three passes at ``0.1`` finish at allowances
  ``0.2``, ``0.1``, then ``0`` when ``stock_to_leave`` is zero. The existing
  ``0.01`` contour safety offset applies to every pass. Zero repeats the
  final contour as before; zero or one finishing pass reserves no additional
  allowance. This is a contour offset, not a maximum radial cutting depth.
- ``stock_to_leave``: material left on the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Plunges, finishing cuts, approaches and retracts are checked against the full
insert footprint and part. Colliding or uncertifiable moves are rejected.
Retracts are exempt from the inward cutting-direction rule.

Use ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)`` to set the machining limits.
With ``add_stock(bounds)``, grooving uses the physical stock envelope for local
radial clearance and safe global entry/exit. Diameter containment assumes
prepared stock within the selected Z range; the complete model remains
protected. Feed approaches and withdrawals are retained. Without the optional
stock envelope, containment-based clearance routing remains.
