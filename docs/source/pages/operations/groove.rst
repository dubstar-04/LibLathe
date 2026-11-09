Grooving
========

``liblathe.op.groove.GrooveOP``

Grooving machines external grooves with a series of radial plunges. The stock
X and Z limits select the area to groove, so a single groove or the whole part
can be machined.

Plunges are spaced evenly along Z, slightly less than the tool's width apart,
so neighbouring plunges overlap by 10% of the tool width. Each depth layer of
``step_over`` is completed across every station before the next, deeper layer
begins. Plunges stop at the part or the stock's minimum X.

The tool always retracts radially out of the stock before moving to the next
Z station. After the plunges, optional finishing passes follow the groove's
walls and floor to remove the small ridges plunges leave on sloped or curved
walls.

Parameters
----------

- ``step_over``: radial depth of each plunge layer.
- ``finish_passes``: number of finishing passes along the final contour.
  Each pass follows the same contour; ``0`` disables them.
- ``stock_to_leave``: material left on the part.
- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Plunges, approaches and retracts are checked against the part.
