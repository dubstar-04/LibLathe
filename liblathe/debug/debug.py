# Add LibLathe is in the Python Path
import os
import sys
import math
from PIL import Image, ImageDraw
import random

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.point import Point
from liblathe.base.boundbox import BoundBox

class Debug:

    def draw(self, segmentgroups):
        """create an image of the segmentgroups"""
        scale = 20
        z_len = 0
        x_len = 0
        ZMin = 0

        for segmentgroup in segmentgroups:
            z_len = max(z_len, segmentgroup.boundbox().ZLength())
            x_len = max(x_len, segmentgroup.boundbox().XLength())
            ZMin = min(ZMin, segmentgroup.boundbox().ZMin)

        width = int(z_len + 10) * scale
        height = int(x_len + 10) * scale

        # creating new Image object
        img = Image.new("RGB", (width, height))

        # create rectangle image
        img1 = ImageDraw.Draw(img)

        image_offset = abs(ZMin) + 5
        for segmentgroup in segmentgroups:
            self.drawSegmentGroup(img1, segmentgroup, image_offset, scale)

        img.show()


    def drawSegmentGroup(self, img, segmentgroup, offset, scale):

            colour = self.get_random_colour()
            lineWidth = 3

            for seg in segmentgroup.getSegments():
                if seg.bulge != 0:
                    radius = seg.getRadius()
                    center = seg.getCentrePoint()

                    z = (center.Z - radius + offset) * scale
                    z1 = (center.Z + radius + offset) * scale
                    x = (center.X - radius) * scale
                    x1 = (center.X + radius) * scale

                    shape = [(z, x), (z1, x1)]

                    start_point = Point(seg.start.Z, seg.start.X)
                    end_point = Point(seg.end.Z, seg.end.X)
                    center_point = Point(center.Z, center.X)

                    dx = start_point.X - center_point.X
                    dz = start_point.Z - center_point.Z
                    start_angle = (math.degrees(math.atan2(dz, dx)) + 360) % 360

                    dx = end_point.X - center_point.X
                    dz = end_point.Z - center_point.Z
                    end_angle = (math.degrees(math.atan2(dz, dx)) + 360) % 360
                    if seg.bulge > 0:
                        img.arc(shape, start=start_angle, end=end_angle, fill=colour, width=lineWidth)
                    if seg.bulge < 0:
                        img.arc(shape, start=end_angle, end=start_angle, fill=colour, width=lineWidth)
                else:
                    img.line([(seg.start.Z + offset) * scale, seg.start.X * scale, (seg.end.Z + offset) * scale, seg.end.X * scale], fill=colour, width=lineWidth)


    def drawQuadtree(self, nodes, segmentGroup):

        bb = segmentGroup.boundbox()
        height = bb.XLength() + 10
        width = bb.ZLength() + 10

        scale = 50

        # creating new Image object
        img = Image.new("RGB", (int(width*scale), int(height*scale)))

        # create rectangle image
        img1 = ImageDraw.Draw(img)

        image_offset = abs(bb.ZMin)

        self.drawSegmentGroup(img1, segmentGroup, image_offset, scale)

        for idx, node in enumerate(nodes):
            x = int((node.center.Z - node.width / 2 + image_offset) * scale)
            x1 = int((node.center.Z + node.width / 2 +  image_offset) * scale)
            y = int((node.center.X - node.height / 2) * scale)
            y1 = int((node.center.X + node.height / 2) * scale)


            shape = (x, y, x1, y1)
            color = "red" if node.sdv < 0 else "green"
            img1.rectangle(shape, fill=None, outline=color)

        img.show()

    def get_random_colour(self):
        """ return a random colour string"""
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)
        colour = '#{:02x}{:02x}{:02x}'.format(r, g, b)
        return colour

    def create_freecad_shape(self, segmentgroup, name):
        """ create a FreeCAD shape for debugging"""

        # return if FreeCAD isn't available
        try:
            import FreeCAD
            import Part
        except ImportError:
            return

        if segmentgroup.count() == 0:
            raise ValueError("Input Segment Group")

        partSegments = []
        for segment in segmentgroup.getSegments():
            start_point = FreeCAD.Vector(segment.start.X, 0, segment.start.Z)
            end_point = FreeCAD.Vector(segment.end.X, 0, segment.end.Z)

            if segment.bulge == 0:
                edge = Part.makeLine(start_point, end_point)
            else:
                center = segment.getCentrePoint()
                axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                start_angle = center.angleTo(segment.start) - 90
                end_angle = center.angleTo(segment.end) - 90
                if segment.bulge > 0:
                    edge = Part.makeCircle(segment.getRadius(),
                                           FreeCAD.Vector(center.X, 0, center.Z),
                                           axis, start_angle, end_angle)
                else:
                    edge = Part.makeCircle(segment.getRadius(),
                                           FreeCAD.Vector(center.X, 0, center.Z),
                                           axis, end_angle, start_angle)

            partSegments.append(edge)

        path_profile = Part.makeCompound(partSegments)
        try:
            FreeCAD.ActiveDocument.removeObject(name)
        except ImportError:
            pass
        finally:
            Part.show(path_profile, name)

    def segmentGroup_to_py(self, segmentgroup):
        """print the segment group to allow use in a python function"""
        print('sg = SegmentGroup()')
        for segment in segmentgroup.getSegments():
            print('sg.addSegment(Segment(Point({:f}, {:f}), Point({:f}, {:f}), {:f}))'
                  .format(segment.start.X, segment.start.Z, segment.end.X, segment.end.Z, segment.bulge))
