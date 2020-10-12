class BoundBox:
    '''
    Generic bounding box implimentation
    '''

    def __init__(self, pt1=None, pt2=None):
        self.XMin = None
        self.YMin = None
        self.ZMin = None
        self.XMax = None
        self.YMax = None
        self.ZMax = None

        if pt1 and pt2:
            self.XMin = min(pt1.X, pt2.X)
            self.YMin = min(pt1.Y, pt2.Y)
            self.ZMin = min(pt1.Z, pt2.Z)
            self.XMax = max(pt1.X, pt2.X)
            self.YMax = max(pt1.Y, pt2.Y)
            self.ZMax = max(pt1.Z, pt2.Z)

    def XLength(self):
        '''
        Return length in x direction
        '''
        return abs(self.XMax - self.XMin)

    def YLength(self):
        '''
        Return length in y direction
        '''
        return abs(self.YMax - self.YMin)

    def ZLength(self):
        '''
        Return length in z direction
        '''
        return abs(self.ZMax - self.ZMin)
