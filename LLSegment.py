import math
from LibLathe.LLPoint import Point


##########################################################
# Based on Paper :An offset algorithm for polyline curves
# By: Xu-Zheng Liu et al
# ISBN: 0166-3615
##########################################################

# https://www.afralisp.net/archive/lisp/Bulges2.htm

class Segment:
    def __init__(self, start=Point(0.0, 0.0, 0.0), end=Point(0.0, 0.0, 0.0), bulge=0.0):
        self.start = start
        self.end = end
        self.bulge = bulge

    def get_angle(self):
        """Returns the included angle between the start and end points"""

        if self.bulge == 0:
            return 180

        return math.atan(self.bulge) * 4

    def set_bulge(self, angle):
        """Sets the bulge of the arc (tan(angle/4))"""

        self.bulge = math.tan(angle / 4)

    def set_bulge_from_radius(self, radius):
        """Sets the bulge of the arc using a known radius"""

        angle = math.asin((self.get_length() * 0.5) / radius) * 2
        self.set_bulge(angle)

    def get_centre_point(self):
        """Returns the centre point of the arc"""

        if self.bulge == 0:
            return None

        # TODO Tidy up this mess!!
        x1 = self.start.X
        y1 = self.start.Z
        x2 = self.end.X
        y2 = self.end.Z
        q = math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1), 2))
        y3 = (y1 + y2) / 2
        x3 = (x1 + x2) / 2

        basex = math.sqrt(math.pow(self.get_radius(), 2) - math.pow((q / 2), 2)) * (y1 - y2) / q
        basey = math.sqrt(math.pow(self.get_radius(), 2) - math.pow((q / 2), 2)) * (x2 - x1) / q

        x = x3 + basex
        z = y3 + basey
        p = Point(x, 0, z)

        return p

    def get_radius(self):
        """Return the radius of the arc"""

        if self.bulge == 0:
            return 0

        rad = self.get_length() * (1 + math.pow(self.bulge, 2)) / (4 * abs(self.bulge))
        return rad

    def get_extent_min(self, direction):
        """Return the minimum value of the segment in direction.
        Direction is a string for the axis of interest, X, Y, Z"""

        values = []
        values.append(getattr(self.start, direction))
        values.append(getattr(self.end, direction))

        if self.bulge != 0:
            centre_pt = getattr(self.get_centre_point(), direction)
            rad = self.get_radius()
            # TODO: Revisit the sign of the offset here. assumes that all lathes use -x
            buldge = centre_pt - rad
            values.append(buldge)

        return min(values, key=abs)

    def get_extent_max(self, direction):
        """Return the maximum value of the segment in direction.
        Direction is a string for the axis of interest, X, Y, Z"""

        values = []
        values.append(getattr(self.start, direction))
        values.append(getattr(self.end, direction))

        if self.bulge != 0:
            centre_pt = getattr(self.get_centre_point(), direction)
            rad = self.get_radius()
            # TODO: Revisit the sign of the offset here. assumes that all lathes use -x
            buldge = centre_pt - rad
            values.append(buldge)

        return max(values, key=abs)

    def get_all_axis_positions(self, direction):
        """Return an array of the axis positions in direction.
        Direction is a string for the axis of interest, X, Y, Z"""

        values = []
        values.append(getattr(self.start, direction))
        values.append(getattr(self.end, direction))

        if self.bulge != 0:
            centre_pt = getattr(self.get_centre_point(), direction)
            rad = self.get_radius()
            # TODO: Revisit the sign of the offset here. assumes that all lathes use -x
            buldge = centre_pt - rad
            values.append(buldge)

        return values

    def get_length(self):
        """Returns the distance between the start and end points"""

        return self.start.distance_to(self.end)

    def get_eta(self):
        """Return eta angle (half the included angle)"""

        return self.get_angle() / 2

    def get_epsilon(self):
        """Returns epsilon angle ()"""

        return math.atan(self.bulge)

    def get_phi(self):
        """Return phi angle"""

        return self.get_gamma() + self.get_epsilon()

    def get_gamma(self):
        """Returns gamma angle"""

        return (math.pi - self.get_angle()) / 2

    def is_same(self, seg):
        """Returns True is the segment is the same"""

        if seg:
            if self.start == seg.start:
                if self.end == seg.end:
                    if self.bulge == seg.bulge:
                        return True

        return False

    def intersect(self, seg, extend=False):

        if self.bulge == 0 and seg.bulge == 0:
            intersect, pt = self.intersectLineLine(seg, extend)
        elif self.bulge != 0 and seg.bulge != 0:
            intersect, pt = self.intersectCircleCircle(seg, extend)
        elif self.bulge != 0 or seg.bulge != 0 and self.bulge == 0 or seg.bulge == 0:
            intersect, pt = self.intersectCircleLine(seg, extend)
        else:
            print('segment.py - Intersect Error with passed segments')

        return intersect, pt

    def intersectLineLine(self, seg, extend=False):

        a1 = self.start
        a2 = self.end
        b1 = seg.start
        b2 = seg.end
        intersect = False
        pt = Point()

        ua_t = (b2.X - b1.X) * (a1.Z - b1.Z) - (b2.Z - b1.Z) * (a1.X - b1.X)
        ub_t = (a2.X - a1.X) * (a1.Z - b1.Z) - (a2.Z - a1.Z) * (a1.X - b1.X)
        u_b = (b2.Z - b1.Z) * (a2.X - a1.X) - (b2.X - b1.X) * (a2.Z - a1.Z)

        if (u_b != 0):
            ua = ua_t / u_b
            ub = ub_t / u_b

            # print('LLSEG intersect', ua, ub)

            if ((0 <= ua and ua <= 1) and (0 <= ub and ub <= 1)) or extend:
                intersect = True
                pt = Point(a1.X + ua * (a2.X - a1.X), 0, a1.Z + ua * (a2.Z - a1.Z))

        return intersect, pt

    def intersectCircleLine(self, seg, extend=False):

        if self.bulge == 0 and seg.bulge != 0:
            line = self
            circle = seg

        if self.bulge != 0 and seg.bulge == 0:
            line = seg
            circle = self

        c = circle.get_centre_point()
        r = circle.get_radius()
        a1 = line.start
        a2 = line.end
        intersect = False
        # pt = Point()
        pts = []
        ptsout = []

        if line.get_length() == 0:
            return intersect, ptsout

        # print('r', r, 'c', c.X, c.Z, 'a1', a1.X, a1.Z, 'a2', a2.X, a2.Z)
        a = (a2.X - a1.X) * (a2.X - a1.X) + (a2.Z - a1.Z) * (a2.Z - a1.Z)
        b = 2 * ((a2.X - a1.X) * (a1.X - c.X) + (a2.Z - a1.Z) * (a1.Z - c.Z))
        cc = c.X ** 2 + c.Z ** 2 + a1.X ** 2 + a1.Z ** 2 - 2 * (c.X * a1.X + c.Z * a1.Z) - r ** 2

        deter = b ** 2 - 4 * a * cc
        # print('deter', deter, a, b, cc, r)
        if deter < 0:
            return intersect, ptsout
        e = math.sqrt(deter)
        u1 = (-b + e) / (2 * a)
        u2 = (-b - e) / (2 * a)

        # print('possible point', u1, u2)
        # pt = Point(u2, 0, u1)

        '''
        if u1 < 0 or u1 > 1 and u2 < 0 or u2 > 1:
                if u1 < 0 and u2 < 0 or u1 > 1 and u2 > 1:
                    #outside
                    if extend:
                        pt = a1.lerp(a2, u1)
                        pt = a1.lerp(a2, u2)
                else:
                #inside
                    if extend:
                        pt = a1.lerp(a2, u1)
                        pt = a1.lerp(a2, u2)
        else:
        '''

        # intersection
        if 0 <= u1 and u1 <= 1 or extend:
            # intersect = True
            pts.append(a1.lerp(a2, u1))

        if 0 <= u2 and u2 <= 1 or extend:
            # intersect = True
            pts.append(a1.lerp(a2, u2))

        # TODO: check that rounding makes sense. possible just add 0.5 to the start and end angle?

        sa = round(c.angle_to(circle.start), 0)
        ea = round(c.angle_to(circle.end), 0)

        if not extend:
            for pnt in pts:
                pnt_ang = round(c.angle_to(pnt), 0)
                # print('arc stuff', sa, ea, pnt_ang, pnt.X, pnt.Z)

                if pnt_ang >= sa and pnt_ang <= ea:
                    # print('point', pnt.X, pnt.Z)
                    # TODO: Return all points and select the nearest in the join_segments function
                    intersect = True
                    ptsout.append(pnt)
        else:
            intersect = True
            ptsout = pts

        return intersect, ptsout

    def intersectCircleCircle(self, seg, extend=False):

        c1 = self.get_centre_point()
        r1 = self.get_radius()
        c2 = seg.get_centre_point()
        r2 = seg.get_radius()
        intersect = False
        pt = Point()
        pts = []

        # Determine minimum and maximum radii where circles can intersect
        r_max = r1 + r2
        r_min = abs(r1 - r2)

        # Determine actual distance between circle centres
        c_dist = c1.distance_to(c2)

        if c_dist > r_max:
            # Intersection Outside
            pass
        elif c_dist < r_min:
            # Intersection Inside
            pass
        else:
            a = (r1 ** 2 - r2 ** 2 + c_dist ** 2) / (2 * c_dist)
            h = math.sqrt(r1 ** 2 - a ** 2)
            p = c1.lerp(c2, a / c_dist)
            b = h / c_dist
            pts.append(Point(p.X - b * (c2.Z - c1.Z), p.Z + b * (c2.X - c1.X)))
            pts.append(Point(p.X + b * (c2.Z - c1.Z), p.Z - b * (c2.X - c1.X)))

            sa1 = c1.angle_to(self.start)
            ea1 = c1.angle_to(self.end)

            sa2 = c2.angle_to(seg.start)
            ea2 = c2.angle_to(seg.end)

            for pnt in pts:
                pnt_ang1 = c1.angle_to(pnt)
                pnt_ang2 = c2.angle_to(pnt)
                # print('arc stuff', sa, ea, pnt_ang, pnt.X, pnt.Z)

                if pnt_ang1 > sa1 and pnt_ang1 < ea1 and pnt_ang2 > sa2 and pnt_ang2 < ea2:
                    # print('point', pnt.X, pnt.Z)
                    intersect = True
                    pt = pnt

        return intersect, pt
