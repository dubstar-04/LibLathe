class BoundBox:
    """Generic bounding box implementation"""

    def __init__(self, pt1=None, pt2=None):
        self.x_min = None
        self.y_min = None
        self.z_min = None
        self.x_max = None
        self.y_max = None
        self.z_max = None

        if pt1 and pt2:
            self.x_min = min(pt1.X, pt2.X)
            self.y_min = min(pt1.Y, pt2.Y)
            self.z_min = min(pt1.Z, pt2.Z)
            self.x_max = max(pt1.X, pt2.X)
            self.y_max = max(pt1.Y, pt2.Y)
            self.z_max = max(pt1.Z, pt2.Z)

    def x_length(self):
        """Return length in x direction"""

        return abs(self.x_max - self.x_min)

    def y_length(self):
        """Return length in y direction"""

        return abs(self.y_max - self.y_min)

    def z_length(self):
        """Return length in z direction"""

        return abs(self.z_max - self.z_min)
