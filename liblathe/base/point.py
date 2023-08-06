import math


class Point:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.X = x
        self.Y = y
        self.Z = z

    def distance_to(self, pt):
        """Returns the distance between two points"""

        return math.sqrt((pt.X - self.X) ** 2 + (pt.Y - self.Y) ** 2 + (pt.Z - self.Z) ** 2)

    def angle_to(self, pt):
        """Returns the angle between two points in degrees"""

        dX = pt.X - self.X
        dZ = pt.Z - self.Z
        angle = (math.degrees(math.atan2(dX, dZ)) + 360) % 360
        return angle

    def nearest(self, pts):
        nearest = Point()
        distance = float('inf')
        for pt in pts:
            if self.distance_to(pt) < distance:
                distance = self.distance_to(pt)
                nearest = pt
        return nearest

    def is_same(self, pt):
        """Returns True if the coordinates are the same"""

        if pt:
            if round(self.X, 5) == round(pt.X, 5):
                if round(self.Y, 5) == round(pt.Y, 5):
                    if round(self.Z, 5) == round(pt.Z, 5):
                        return True

        return False

    def sub(self, pt):
        """Returns a point with the difference between self and pt"""

        p = Point(self.X - pt.X, self.Y - pt.Y, self.Z - pt.Z)
        return p

    def add(self, pt):
        """Returns a point addition between self and pt"""

        p = Point(self.X + pt.X, self.Y + pt.Y, self.Z + pt.Z)
        return p

    def multiply(self, val):
        """Returns a point multiplication between self and val"""

        p = Point(self.X * val, self.Y * val, self.Z * val)
        return p

    def lerp(self, pt, t):
        """Returns a point linear interpolation between self and pt
        t is parameter [0 1] for the distance between self and pt
        e.g. t = 0.5 will return midpoint between self and pt"""

        p = Point(self.X + (pt.X - self.X) * t, self.Y + (pt.Y - self.Y) * t, self.Z + (pt.Z - self.Z) * t)
        return p

    def normalise_to(self, pnt):
        """returns the normalised direction from self to pt"""
        p = pnt.sub(self)
        m = math.sqrt(p.X ** 2 + p.Y ** 2 + p.Z ** 2)
        if m == 0:
            return Point(0.0, 0.0, 0.0)
        else:
            return Point(p.X / m, p.Y / m, p.Z / m)

    def rotate(self, angle):
        """Returns a point rotated by angle in degrees"""
        # TODO: rotate should operate about another point.
        angle = math.radians(angle)

        x = self.X * math.cos(angle) - self.Z * math.sin(angle)
        z = self.X * math.sin(angle) + self.Z * math.cos(angle)
        p = Point(x, self.Y, z)
        return p

    def mid(self, pt):
        """Returns midpoint between self and pt"""

        x = (self.X + pt.X) / 2
        y = (self.Y + pt.Y) / 2
        z = (self.Z + pt.Z) / 2
        p = Point(x, y, z)
        return p

    def project(self, angle, distance):
        """Project the point at angle by distance"""

        angle = math.radians(angle)
        x = round(self.X + math.sin(angle) * distance, 5)
        z = round(self.Z + math.cos(angle) * distance, 5)
        p = Point(x, self.Y, z)
        return p
