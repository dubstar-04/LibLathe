Geometry
========

LibLathe uses a simplified geometry representation which consists of a single
type; the segment. This geometry is used throughout LibLathe to hold the part
and path representations.

.. figure:: /LL_static/images/geometry.png
    :align: center
    :figwidth: 600px
    :target: /LL_static/images/geometry.png

The Segment
+++++++++++
The segment is the fundamental representation of LibLathe geometry. The segment 
can represent one of two basic forms; A line segment or an arc segment.

.. figure:: /LL_static/images/segment.png
    :align: center
    :figwidth: 350px
    :target: /LL_static/images/segment.png

Grouping the geometry into a single type is possible as both lines and arcs can
be defined by three components: 

- Start Point
- End Point
- Bulge

This method of segment representation is inspired by a technical paper 
titled **An offset algorithm for polyline curves** by Xu-Zheng Liu et al, ISBN: 0166-3615

Line Segments
-------------
Line segments are represented by two points; a start point and an end point, 
the buldge value is always equal to zero for line segments. 


Arc Segments
------------
Arc segments are more complicated than line segments, however using the segment
method arcs can be simplified to a three component representation.
As with lines arcs also need start and end points, arcs however require a non-zero 
bulge value

Bulge values are calculated:

 ``bulge = tan(angle/4)``
 
where;
angle is the central arc angle between the start and end points. 


The Segment Group
+++++++++++++++++

.. figure:: /LL_static/images/segment_group.png
    :align: center
    :figwidth: 600px
    :target: /LL_static/images/segment_group.png

The segment group is a container object that holds a collection of segments, usually 
representing a 'pass'. The segment group can perform a set of operations on the segments
such as: 

- Offsetting
- Converting to gcode
- Analysis for use with a selected tool