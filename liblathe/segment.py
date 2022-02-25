import math
from liblathe.boundbox import BoundBox

from liblathe.point import Point


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
        """Returns the included angle between the start and end points in radians"""
        #TODO: Is this supposed to return 0 to 2 * math.pi?

        if self.bulge == 0:
            return math.pi

        return math.atan(abs(self.bulge)) * 4

    def set_bulge(self, angle):
        """
        Sets the bulge of the arc (tan(angle/4))
        Negative bulge = clockwise
        Positive bulge = anticlockwise
        angle in radians
        """

        self.bulge = math.tan(angle / 4)

    def get_centre_point(self):
        """Returns the centre point of the arc"""
        
        midp = self.start.mid(self.end)
        
        if self.bulge == 0:
            return midp
        
        a = self.get_apothem()

        # check if the center point is inverted. i.e. at 180 it goes inside the arc
        if self.get_angle() > math.pi:
            a = -a

        centre_pt = midp.project(self.get_rotation() - 90, a)

        if self.bulge > 0:
            centre_pt = midp.project(self.get_rotation() + 90, a)

        return centre_pt

    def get_radius(self):
        """Return the radius of the arc"""

        if self.bulge == 0:
            return 0

        rad = self.get_length() * (1 + math.pow(self.bulge, 2)) / (4 * abs(self.bulge))
        return rad

    def get_rotation(self):
        """returns the rotation of the segment"""
        return self.start.angle_to(self.end)

    def get_boundbox(self):

        if self.bulge == 0:

            pt1 = self.start
            pt2 = self.end

        else:

            #TODO: Make this more sexy

            startAngle = min(self.get_centre_point().angle_to(self.start), self.get_centre_point().angle_to(self.end))
            endAngle = max(self.get_centre_point().angle_to(self.start), self.get_centre_point().angle_to(self.end))

            if self.get_angle() > math.pi:
                endAngle = min(self.get_centre_point().angle_to(self.start), self.get_centre_point().angle_to(self.end))
                startAngle = max(self.get_centre_point().angle_to(self.start), self.get_centre_point().angle_to(self.end))

            cross0 = startAngle%360 >= endAngle%360
            cross90 = (startAngle - 90)%360 >= (endAngle - 90)%360
            cross180 = (startAngle - 180)%360 >= (endAngle - 180)%360
            cross270 = (startAngle - 270)%360 >= (endAngle - 270)%360

            startX = self.get_radius() * math.cos(math.radians(startAngle))
            startY = self.get_radius()  * math.sin(math.radians(startAngle))
            endX = self.get_radius()  * math.cos(math.radians(endAngle))
            endY = self.get_radius()  * math.sin(math.radians(endAngle))

            right = self.get_radius() if cross0 else max(startX, endX)
            bottom = self.get_radius() if cross90 else max(startY, endY)
            left = -self.get_radius() if cross180 else min(startX, endX)
            top = -self.get_radius() if cross270 else min(startY, endY)

            xmin = top + self.get_centre_point().X
            xmax = bottom + self.get_centre_point().X
            zmin = left + self.get_centre_point().Z
            zmax = right + self.get_centre_point().Z

            pt1 = Point(xmin, 0, zmin)
            pt2 = Point(xmax, 0, zmax)
     
        boundbox = BoundBox(pt1, pt2)
        return boundbox


    def get_length(self):
        """Returns the distance between the start and end points"""
        # TODO: Arc length should be the true length not the distance between the start and endpoints?
        return self.start.distance_to(self.end)

    def get_sagitta(self):
        """Returns the arc height, typically referred to as the sagitta"""
        return self.get_length / 2 * self.bulge

    def get_apothem(self):
        """Returns apothem. distance from arc center to cord midpoint"""
        return math.sqrt(pow(self.get_radius(), 2) - pow(self.get_length() / 2, 2))

    def get_eta(self):
        """Return eta angle (half the included angle) in radians"""

        return self.get_angle() / 2

    def get_epsilon(self):
        """Returns signless epsilon angle in radians"""
        if self.bulge == 0:
            return 0

        return abs(math.atan(self.bulge))

    def get_phi(self):
        """Return signless phi angle in radians"""

        if self.bulge == 0:
            return 0

        return abs((math.pi - abs(self.get_angle()) / 2) / 2)

    def get_gamma(self):
        """Returns signless gamma angle in radians"""

        if self.bulge == 0:
            return 0

        return (math.pi - abs(self.get_angle())) / 2

    def is_same(self, seg):
        """Returns True is the segment is the same"""

        if seg:
            if self.start == seg.start:
                if self.end == seg.end:
                    if self.bulge == seg.bulge:
                        return True

        return False

    def offset(self, distance):
        """Returns a new segment offset by distance"""

        if self.bulge != 0:

            if self.bulge > 0:

                # can't offset because the distance is bigger than the radius
                if self.get_radius() < distance:
                    return None
                    
                # get normal from end point to centre
                start_normal = self.start.normalise_to(self.get_centre_point())
                end_normal = self.end.normalise_to(self.get_centre_point())
            else:
                # get normal from the centre to the end points
                start_normal = self.get_centre_point().normalise_to(self.start)
                end_normal = self.get_centre_point().normalise_to(self.end)

            pt1 = start_normal.multiply(distance)
            pt2 = end_normal.multiply(distance)
            new_start = pt1.add(self.start)
            new_end = pt2.add(self.end)

            angle = self.angle_from_points(new_start, new_end)
            seg = Segment(new_start, new_end)

            if self.bulge:
                seg.set_bulge(angle)

        else:
            normal = self.start.normalise_to(self.end).rotate(-90)
            pt = normal.multiply(distance)
            seg = Segment(pt.add(self.start), pt.add(self.end))

        return seg

    def angle_from_points(self, new_start, new_end):
        """
        Get the new angle for a segment using new start and end points
        returned angle can be used to set the new bulge using .set_bulge(new_angle)
        """
    
        if self.bulge == 0:
            return math.pi

        centre_pt = self.get_centre_point()
        startAngle = centre_pt.angle_to(new_start)
        endAngle = centre_pt.angle_to(new_end)

        if self.bulge > 0:
            totalAng = endAngle - startAngle
        else:
            totalAng = startAngle - endAngle

        incAng = math.copysign((totalAng - 360)%360, self.bulge)

        return math.radians(incAng)

    def intersect(self, seg, extend=False):
        """Determine intersections between self and seg"""
        if self.bulge == 0 and seg.bulge == 0:
            intersect, pt = self.intersect_line_line(seg, extend)
        elif self.bulge != 0 and seg.bulge != 0:
            intersect, pt = self.intersect_circle_circle(seg, extend)
        elif self.bulge != 0 or seg.bulge != 0 and self.bulge == 0 or seg.bulge == 0:
            intersect, pt = self.intersect_circle_line(seg, extend)
        else:
            print('segment.py - Intersect Error with passed segments')

        # TODO: this should return a nt type not Point() or []
        return intersect, pt

    def intersect_line_line(self, seg, extend=False):
        """Determine intersections between self and seg when both are line segments"""

        a1 = self.start
        a2 = self.end
        b1 = seg.start
        b2 = seg.end
        intersect = False
        pts = []

        ua_t = (b2.X - b1.X) * (a1.Z - b1.Z) - (b2.Z - b1.Z) * (a1.X - b1.X)
        ub_t = (a2.X - a1.X) * (a1.Z - b1.Z) - (a2.Z - a1.Z) * (a1.X - b1.X)
        u_b = (b2.Z - b1.Z) * (a2.X - a1.X) - (b2.X - b1.X) * (a2.Z - a1.Z)

        if (u_b != 0):
            ua = ua_t / u_b
            ub = ub_t / u_b

            if ((0 <= ua and ua <= 1) and (0 <= ub and ub <= 1)) or extend:
                intersect = True
                pt = Point(a1.X + ua * (a2.X - a1.X), 0, a1.Z + ua * (a2.Z - a1.Z))
                pts.append(pt)

        return intersect, pts

    def intersect_circle_line(self, seg, extend=False):
        """Determine intersections between self and seg when one is a line segment and one is an arc segment"""

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

        # intersection
        if 0 <= u1 and u1 <= 1 or extend:
            pts.append(a1.lerp(a2, u1))

        if 0 <= u2 and u2 <= 1 or extend:
            pts.append(a1.lerp(a2, u2))

        if not extend:
            for pnt in pts:
                # check if the point is on the segment
                if circle.point_on_segment(pnt):
                    ptsout.append(pnt)

        else:
            intersect = True
            ptsout = pts
        # TODO: Return all points and select the nearest in the join_segments function

        if len(ptsout):
            intersect = True

        return intersect, ptsout

    def intersect_circle_circle(self, seg, extend=False):
        """Determine intersections between self and seg when both are arc segments"""
        # ref http://paulbourke.net/geometry/circlesphere/

        c1 = self.get_centre_point()
        r1 = self.get_radius()
        c2 = seg.get_centre_point()
        r2 = seg.get_radius()
        intersect = False
        pts = []
        ptsout = []

        # Determine actual distance between circle centres
        c_dist = c1.distance_to(c2)

        if round(c_dist, 5) >= round(r1 + r2, 5):
            # too far apart to intersect or just touching
            return intersect, ptsout

        if c_dist < abs(r1 - r2):
            # inside each other
            return intersect, ptsout

        if c1.is_same(c2) or round(c_dist, 5) == 0:
            # concentric
            return intersect, ptsout

        # get the chord distance
        a = (r1 ** 2 - r2 ** 2 + c_dist ** 2) / (2 * c_dist)

        # A**2 + B**2 = C**2; h**2 + a**2 = r1**2 therefore:
        h = math.sqrt(r1 ** 2 - a ** 2)
        p = c1.lerp(c2, a / c_dist)
        b = h / c_dist
        pts.append(Point(p.X - b * (c2.Z - c1.Z), 0, p.Z + b * (c2.X - c1.X)))
        pts.append(Point(p.X + b * (c2.Z - c1.Z), 0, p.Z - b * (c2.X - c1.X)))

        for pnt in pts:
            # check if the point is on both segments
            if self.point_on_segment(pnt) and seg.point_on_segment(pnt):
                ptsout.append(pnt)

        if len(ptsout):
            intersect = True

        return intersect, ptsout

    def point_on_segment(self, point):
        """Determine if point is on self"""

        if self.bulge == 0:
            # Line
            # TODO: Move the line code here
            pass
        else:
            # Arc
            c = self.get_centre_point()
            radius = self.get_radius()
            sa = c.angle_to(self.start)
            ea = c.angle_to(self.end)
            pnt_ang = c.angle_to(point)

            # if the point isn't on the segment radius it's not a true intersection
            if round(c.distance_to(point), 5) != round(radius, 5):
                return False

            # print('point_on_segment', pnt_ang, 'X:', point.X, 'Y:', point.Y, 'Z:', point.Z)
            # print('point_on_segment arc:, sa:',sa, 'ea:', ea)
            # print("centre point", c.X, c.Z)

            # TODO: There must be a slicker way to Determine if the point is on the arc. Current method good for debug.

            if self.bulge > 0:
                if sa < ea:
                    #print('sa < ea - positive bulge')
                    if pnt_ang >= sa and pnt_ang <= ea:
                        return True

                if sa > ea:
                    #print('sa > ea - positive bulge')
                    if pnt_ang >= sa or pnt_ang <= ea:
                        return True

            elif self.bulge < 0:
                if sa < ea:
                    #print('sa > ea - negative bulge')
                    if pnt_ang <= sa or pnt_ang >= ea:
                        return True

                if sa > ea:
                    #print('sa > ea - negative bulge')
                    if pnt_ang <= sa and pnt_ang >= ea:
                        return True
