Grooving
========

``liblathe.op.groove.GrooveOP``

Grooving machines external grooves with a series of radial plunges. The stock
X and Z limits select the area to groove, so a single groove or the whole part
can be machined.

Plunges are spaced evenly along Z, slightly less than the tool's width apart,
so neighbouring plunges overlap by 10% of the tool width. Each depth layer of
``pass_offset`` is completed across every station before the next, deeper layer
begins. Plunges stop at the part or the stock's minimum X.

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

- ``pass_offset``: radial depth of each plunge layer.
- ``finish_passes``: number of finishing passes along the final contour.
  Each pass completes all inward-oriented strokes along the same contour;
  ``0`` disables them. This counts complete contours, not individual strokes.
- ``stock_to_leave``: material left on the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Plunges, finishing cuts, approaches and retracts are checked against the full
insert footprint and part. Colliding or uncertifiable moves are rejected.
Retracts are exempt from the inward cutting-direction rule.
