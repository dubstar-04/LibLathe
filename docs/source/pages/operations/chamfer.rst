Chamfer edge breaks
===================

``liblathe.op.chamfer.ChamferOP`` creates equal-distance, 45-degree breaks on
sharp axial/radial corners selected by profile vertex index. It does not follow
existing chamfer faces. Each selected corner receives one or more cutting passes.

Parameters
----------

* ``chamfer_size``: positive finite distance along **each adjacent face**, in mm;
  defaults to 1.0. This is not the diagonal width or a diameter increment.
* ``pass_offset``: positive finite maximum infeed perpendicular to the chamfer,
  including the first pass from the sharp corner. Passes are evenly spaced and
  the last reaches the requested size. Defaults to 0.25 mm.
* ``corner_indices``: non-empty list or tuple of unique profile vertex indices.
  Index 0 is the first segment's start; index N is the last of N segments' end.
  Intermediate indices identify connected segment junctions.
* ``mode``: ``MachiningMode.EXTERNAL`` or ``MachiningMode.INTERNAL``.
* ``direction``: must be ``Direction.RADIAL``; chamfer passes always use radial
  approach and routing.
* ``chamfer_position``: ``ChamferPosition.FRONT`` or ``ChamferPosition.BACK``,
  defined in ``liblathe.op.chamfer``. This is descriptive metadata only; it does
  not select or anchor a corner to the containment limits. ``corner_indices``
  selects the exact profile vertices. External cuts always travel from Radial
  Max to Radial Min; internal cuts always travel from Radial Min to Radial Max,
  regardless of position. Defaults to ``FRONT``.
* ``clearance``, ``hfeed`` and ``vfeed``: shared routing/feed settings.

For example, an external profile running from (0, 0) to (10, 0) to (10, -20)
has its front outer corner at index 1::

    from liblathe.op.chamfer import ChamferOP, ChamferPosition

    operation = ChamferOP()
    operation.setParams({
        "chamfer_size": 0.5,
        "pass_offset": 0.1,
        "chamfer_position": ChamferPosition.FRONT,
        "corner_indices": (1,),
    })
    operation.addPartSegments(part_segments)
    operation.add_containment(bounds)
    operation.add_stock(stock_bounds)
    operation.add_tool(tool)
    commands = operation.getGCode()

Internal profiles may start at the bore mouth without an explicit face segment;
index 0 uses the profile's radial closure as the mouth face. Near/Far signed
coordinates and Internal mode use the standard BaseOP reflections without
changing vertex indices.

Geometry and validation
-----------------------

Only convex, right-angle junctions between straight axial and radial faces are
supported. Axis corners, arcs, concave corners, oversized or overlapping breaks
are rejected. The size must leave some of each adjacent face.

The complete insert outline, including circular nose extrema, determines the
tool-reference translation. A 0.0001 mm outward normal margin keeps tangent
positions outside native boundary classification. Complete sweeps are certified
in 0.001 mm spans (one tenth of the native scan resolution), without subdividing
the emitted straight cut. For rounded inserts near straight faces, supporting-circle
separation can certify clearance without exhausting adaptive subdivision.
The original part outline is unchanged by generation.

Cuts, approaches and withdrawals are checked against the part with the current
and earlier passes removed, not against material those passes intentionally cut.
Containment must include the **whole compensated break**; the operation rejects
clipping rather than silently leaving an incomplete chamfer. Inaccessible
inserts or routes raise errors and clear published paths.

External radial approaches and withdrawals feed between the cut and the outer
stock or part boundary, allowing for the insert reference point. Extra containment
needed for compensation does not extend these feeds. Repositioning beyond that
boundary uses rapid moves and the configured clearance.

These checks do not certify remaining stock, a pre-existing bore, bar/holder
clearance, fixtures or machine travel. Review postprocessed output and tool setup
before machining.
