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


class Debug:

    def draw(self, segmentgroups):
        """create an image of the segmentgroups"""
        scale = 20
        z_len = 0
        x_len = 0
        z_min = 0

        for segmentgroup in segmentgroups:
            z_len = max(z_len, segmentgroup.boundbox().z_length())
            x_len = max(x_len, segmentgroup.boundbox().x_length())
            z_min = min(z_min, segmentgroup.boundbox().z_min)

        width = int(z_len + 10) * scale
        height = int(x_len + 10) * scale
        
        # creating new Image object
        img = Image.new("RGB", (width, height))

        # create rectangle image
        img1 = ImageDraw.Draw(img)

        image_offset = abs(z_min) + 5

        for segmentgroup in segmentgroups:
            colour = self.get_random_colour()
            for seg in segmentgroup.get_segments():
                if seg.bulge != 0:
                    radius = seg.get_radius()
                    center = seg.get_centre_point()

                    z = (center.z - radius + image_offset) * scale
                    z1 = (center.z + radius + image_offset) * scale
                    x = (center.x - radius) * scale
                    x1 = (center.x + radius) * scale

                    shape = [(z, x), (z1, x1)] 

                    start_point = Point(seg.start.z, seg.start.x)
                    end_point = Point(seg.end.z, seg.end.x)
                    center_point = Point(center.z, center.x)

                    dx = start_point.x - center_point.x 
                    dz = start_point.z - center_point.z
                    start_angle = (math.degrees(math.atan2(dz, dx)) + 360) % 360

                    dx = end_point.x - center_point.x
                    dz = end_point.z - center_point.z
                    end_angle = (math.degrees(math.atan2(dz, dx)) + 360) % 360
                    if seg.bulge > 0:
                        img1.arc(shape, start=start_angle, end=end_angle, fill=colour)
                    if seg.bulge < 0:
                        img1.arc(shape, start=end_angle, end=start_angle, fill=colour)
                else:
                    img1.line([(seg.start.z + image_offset) * scale, seg.start.x * scale, (seg.end.z + image_offset) * scale, seg.end.x * scale], fill=colour, width=2)

        img.show()

    def get_random_colour(self):
        """ return a random colour string"""
        r = random.randint(50, 255)
        colour = '#{:02x}{:02x}{:02x}'.format(r, r, r)
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

        part_edges = []
        for segment in segmentgroup.get_segments():
            start_point = FreeCAD.Vector(segment.start.x, 0, segment.start.z)
            end_point = FreeCAD.Vector(segment.end.x, 0, segment.end.z)

            if segment.bulge == 0:
                edge = Part.makeLine(start_point, end_point)
            else:
                center = segment.get_centre_point()
                axis = FreeCAD.Vector(0.0, 1.0, 0.0)
                start_angle = center.angle_to(segment.start) - 90
                end_angle = center.angle_to(segment.end) - 90
                if segment.bulge > 0:
                    edge = Part.makeCircle(segment.get_radius(),
                                           FreeCAD.Vector(center.x, 0, center.z),
                                           axis, start_angle, end_angle)
                else:
                    edge = Part.makeCircle(segment.get_radius(),
                                           FreeCAD.Vector(center.x, 0, center.z),
                                           axis, end_angle, start_angle)

            part_edges.append(edge)

        path_profile = Part.makeCompound(part_edges)
        try:
            FreeCAD.ActiveDocument.removeObject(name)
        except ImportError:
            pass
        finally:
            Part.show(path_profile, name)

    def segment_group_to_py(self, segmentgroup):
        """print the segment group to allow use in a python function"""
        print('sg = SegmentGroup()')
        for segment in segmentgroup.get_segments():
            print('sg.add_segment(Segment(Point({:f}, {:f}), Point({:f}, {:f}), {:f}))'
                  .format(segment.start.x, segment.start.z, segment.end.x, segment.end.z, segment.bulge))
