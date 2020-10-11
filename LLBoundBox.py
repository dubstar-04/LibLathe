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
        
        if pt1:
            self.XMin = pt1.X
            self.YMin = pt1.Y
            self.ZMin = pt1.Z

        if pt2:
            self.XMax = pt2.X
            self.YMax = pt2.Y
            self.ZMax = pt2.Z


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