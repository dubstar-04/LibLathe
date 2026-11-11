Parting
=======

``liblathe.op.partoff.PartoffOP``

.. figure:: /LL_static/images/PartingOp.jpeg
    :align: center
    :figwidth: 450px

Parting cuts the finished part off the stock. It is a single radial pass from
containment's maximum X down to its minimum X, at its minimum Z.
These are tool-reference coordinates: the insert's width no longer shifts the
cut beyond the selected minimum Z. Set that limit to the desired reference depth.

Set machining limits with ``add_containment(bounds)`` or
``add_containment_from_limits(xmin, xmax, zmin, zmax)``.

Parameters
----------

- ``clearance``: distance kept between the tool and the stock on rapid moves.
- ``hfeed``: feed rate.

Set the containment's minimum X to zero to part the component off completely.
Approach and withdrawal feeds also remain inside containment. The tool withdraws
radially through the kerf after the cut; axial repositioning
occurs at radial stock clearance, never as a feed through the component.
Rapids connect the containment boundary to clearance and may cross the original
stock envelope. Users must assess remaining stock before machining. Supply
physical stock with ``add_stock(bounds)`` for initial clearance positioning.
