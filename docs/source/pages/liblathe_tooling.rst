LibLathe Tooling
========================================

.. figure:: /LL_static/images/tool.png
    :align: center
    :figwidth: 600px
    :target: /LL_static/images/tool.png


Turning inserts
++++++++++++++++++++++++++++++++++++++++
LibLathe tools describe turning inserts. For insert codes and dimensions,
refer to :doc:`turning_inserts`.

Native outlines and origins
----------------------------------------

Use ``Tool.set_tool_from_segments(segments)`` to supply the actual insert
outline as XZ ``Segment`` objects, retaining rounded nose arcs. X is radial;
Z is axial. In the plotted view, +X points down and +Z points right. The
integration defines how these coordinates relate to the machine.

The outline's origin is the tool reference positioned by the generated path.
It need not be the theoretical sharp tip or the nose-circle centre. LibLathe
uses the supplied outline directly; it does not select or shift its datum.
For example, FreeCAD's Turning Addon builds its chosen Compensation origin
into the native outline before passing it to LibLathe. That selector belongs
to the add-on, not this library, and is not controller G41/G42 compensation.

Supply the insert in its actual angular pose. Keep ``tool_rotation`` at zero
when that rotation is already included in the outline. A nonzero value is an
additional rotation, in degrees, around the supplied origin, applied by
``get_segmentgroup()``. Do not confuse it with the add-on's absolute insert
angle, the legacy ``ToolOri`` construction setting, or a controller Q type.
Changing tool side does not choose a cutting corner or rotate the stored insert.

Tool side
---------

``Tool.side`` requires an enum member, not a string:

.. code-block:: python

     from liblathe.tool.tool import Tool, ToolSide

     tool = Tool()
     assert tool.side is ToolSide.NEAR
     tool.side = ToolSide.FAR

This example selects the side only. Before planning, supply the tool outline,
part and stock in the matching physical coordinate frame.

* ``ToolSide.NEAR`` is the default, using the ordinary positive-X planning path.
* ``ToolSide.FAR`` requires negative-X stock and part geometry. Positive-X
    inputs are rejected within the existing coordinate tolerance.

For Far, ``BaseOP.getGCode()`` reflects copies of the part, stock and posed
insert into a positive-X planning frame. It then reflects the generated
commands and ``tool_paths`` back to the physical negative-X frame. Original
inputs are not changed. Segment reflection negates X coordinates and bulges.

Far-side output transformations:

* X positions are negated, including rapid and retract moves.
* I radial arc-centre offsets are negated.
* G2 and G3 are swapped, including G02 and G03 spellings.
* Z, K and feed values are unchanged.

Far output remains negative X; it is not converted into positive-radius
controller output. A postprocessor or machine integration must respect this
contract. The enum is a development API: older packages reporting version
0.0.8 may not provide ``ToolSide``. Strings are not compatibility aliases.

Spindle and machining limits
----------------------------------------

Side does not select spindle speed, M3/M4, tool handedness, or G41/G42.
In FreeCAD, spindle settings belong to the Tool Controller. Physical post
alone is insufficient to infer the required spindle direction.

Near/Far is not outside/inside machining. Internal boring requires separate
operation support. Signed-side planning remains experimental. Existing sweep
and clearance checks do not certify holders, fixtures, unknown initial-position
travel or complete machining safety, and do not establish reference-equivalent
Profile final stock. See the repository README for the current guarantees and
limitations, and :doc:`operations` for the available operation classes.
