from liblathe.base.point import Point

class Node:
    """A node centred at (cx, cy) with width w and height h."""

    def __init__(self, center = Point(), w=1, h=1):
        self.center = center
        self.w = w 
        self.h = h
        '''
        self.north_edge = cy - h/2
        self.east_edge =  cx + w/2
        self.south_edge =  cy + h/2
        self.west_edge = cx - w/2
        '''
class Quadtree:
    def __init__(self, node, segment_group, img, precision=0.1, target=0.25, limit=2, depth=0):
        self.target = target
        self.limit = limit
        self.precision = precision
        self.node = node
        self.signed_value = None
        self.divided = False
        self.segment_group = segment_group
        self.depth = depth

        self.img = img

        self.conquer()

    def conquer(self):
        """Divide each node until the target precision is reached"""
        # get signed value if less than limit, divide and conquer
        # until a the precision limit is reached
        self.signed_value = self.segment_group.sdv(self.node.center)
        # print('depth', self.depth, 'node', self.signed_value, 'w', self.node.w, 'h', self.node.h, 'x', self.node.center.X , 'z', self.node.center.Z)
        
        self.draw()

        # turning parameters
        stepover = 0.25
        passes = 5

        offset = stepover * passes * 1.5

        if self.divided:
            return
        
        if self.node.w <= 0.2:
            return
        
        if self.depth >= 3 and abs(self.signed_value) > offset * 3:
            return
        
        if self.depth < 6 or self.signed_value > 0 and self.signed_value < offset * 2.5:
            self.divide()

        if self.signed_value < 0 and abs(self.signed_value) < offset:
            self.divide()

        '''
        if self.depth >= 4 and abs(self.signed_value) > offset * 2:
            return

        if self.node.h <= 0.01:
            return

        modulo = 0.03
        if self.depth < 4 or (stepover - (self.signed_value)) % stepover < modulo or (self.signed_value) % stepover < modulo:            
            self.divide()
        '''


    def draw(self):

        tz = ((self.node.center.Z - self.node.w / 2) + 60 )* 10
        tx = (self.node.center.X - self.node.h / 2) * 10
        shape = [(tz, tx), (tz + self.node.w * 10, tx + self.node.h * 10)]
        colour = "#ffff33"
        if self.signed_value < 0:
            colour = "#00ffff"
        self.img.rectangle(shape, outline = colour)


    def divide(self):
        """Divide (branch) this node by spawning four children nodes."""

        cx = self.node.center.X
        cy = self.node.center.Z
        w = self.node.w / 2
        h = self.node.h / 2

        self.ne = Quadtree(Node(Point(cx - h/2, 0, cy + w/2), w, h),
                                    self.segment_group, self.img, self.precision, self.target, self.limit, self.depth+1)
        self.se = Quadtree(Node(Point(cx + h/2, 0, cy + w/2), w, h),
                                    self.segment_group, self.img, self.precision, self.target, self.limit, self.depth+1)
        self.sw = Quadtree(Node(Point(cx + h/2, 0, cy - w/2), w, h),
                                    self.segment_group, self.img, self.precision, self.target, self.limit, self.depth+1)
        self.nw = Quadtree(Node(Point(cx - h/2, 0, cy - w/2), w, h),
                                    self.segment_group, self.img, self.precision, self.target, self.limit, self.depth+1)

        self.divided = True

    def query(self, target, found_points=[]):
        """Find the points in the quadtree that are close to target value"""

        dist = round(self.signed_value, 2)
        if dist >= target and dist <= target + 0.05:
            found_points.append(self.node.center)

        if self.divided:
            self.nw.query(target, found_points)
            self.ne.query(target, found_points)
            self.se.query(target, found_points)
            self.sw.query(target, found_points)

        return found_points
