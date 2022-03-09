Bulge
======

LibLathe uses a simplified geometry representation which consists of a single
type; the segment. Segments consist of 3 bit of data:

- Start Point
- End Point
- Bulge

These 3 bits of data give Liblathe all the information required to calculate the position, size and direction of 
lines and arcs.


.. figure:: /LL_static/images/bulge.png
    :align: center
    :figwidth: 600px
    :target: /LL_static/images/bulge.png

|
| Bulge values are calculated:

``bulge = tan(theta/4)``

| theta is the central arc angle between the start and end points.

Direction:

``bulge > 0 = CCW`` and ``bulge < 0 = CW``

| Positive bulge values represent arcs with a counter clockwise direction
| Negative bulge values represent arcs with a clockwise direction
| Segments where the bulge is equal to zero represent a line


Parameters:
+++++++++++

+---------+------------------------------------+
| Name    | Description                        |
+=========+====================================+
| theta   | included angle                     |
+---------+------------------------------------+
| eta     | half included angle                |
+---------+------------------------------------+
| epsilon | quarter included angle             |
+---------+------------------------------------+
| phi     | pi - epsilon                       |
+---------+------------------------------------+
| gamma   | pi - eta                           |
+---------+------------------------------------+
| tau     | see phi                            |
+---------+------------------------------------+
| radius  | distance between start and end / 2 |
+---------+------------------------------------+
| sagitta | arc height                         |
+---------+------------------------------------+
| apothem | radius - sagitta                   |
+---------+------------------------------------+



