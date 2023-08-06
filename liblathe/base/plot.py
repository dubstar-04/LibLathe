import math
import os

from PIL import Image, ImageDraw, ImageOps

from liblathe.base.point import Point
from liblathe.base.command import Command


class Plot:
    def __init__(self):
        self.background = (168, 168, 168)
        self.transparency = False
        self.file_location = ''
        self.image_name = 'image1'
        self.image_type = '.jpg'
        self.image_size = (1920, 1080)
        self.mirror_image = False
        self.flip_image = False
        self.g0_colour = (256, 0, 0)
        self.g1_colour = (0, 256, 0)
        self.g2_colour = (0, 256, 0)
        self.g3_colour = (0, 256, 0)
        self.line_thickness = 2
        self.margin = 100
        self.draw = None

        self._min_x = 500000
        self._min_y = 500000
        self._max_x = -500000
        self._max_y = -500000

    def set_file_path(self, path):
        """Specify the location to save the plotted image"""
        if os.path.exists(path):
            self.file_location = path
        else:
            raise Warning('Given file path does not exist!')

    def set_transparency(self):
        """Set transparency on/off"""
        self.transparency = not self.transparency

    def set_background_colour(self, colour):
        """"Set background colour of image"""
        if isinstance(colour, tuple) and len(colour) == 3:
            try:
                self.background = colour
            except Exception:
                raise Warning('Unknown colour! Colour is RGB. For example (255, 255, 255)')

    def set_path_colour(self, g_number, colour):
        """Set the colour of g path. For example G0, (255,255,255)"""
        if isinstance(colour, tuple) and len(colour) == 3:
            try:
                if g_number.upper().startswith('G0'):
                    self.g0_colour = colour
                elif g_number.upper().startswith('G1'):
                    self.g1_colour = colour
                elif g_number.upper().startswith('G2'):
                    self.g2_colour = colour
                elif g_number.upper().startswith('G3'):
                    self.g3_colour = colour
            except Exception:
                raise Warning('Unknown value! Please use for example G0, (255,255,255)')
        else:
            raise Warning('Unknown colour! Colour is RGB. For example (255, 255, 255)')

    def flip_image_horizontal(self):
        """Flip image horizontally(left to right).Turns On/Off"""
        self.mirror_image = not self.mirror_image
        self.flip_image = False

    def flip_image_vertical(self):
        """Flip the image vertically(top to bottom). Turns On/Off"""
        self.flip_image = not self.flip_image
        self.mirror_image = False

    def _plot_segment_groups(self, segment_groups):
        """
        Convert an image from supplied geometry
        Valid input: List of type liblathe.segmentgroup
        """

        line_colour = self._get_line_colour("G1")

        for segment_group in segment_groups:

            segments = segment_group.get_segments()

            for seg in segments:
                start = self._translate_point(Point(seg.start.Z, seg.start.X))
                end = self._translate_point(Point(seg.end.Z, seg.end.X))

                if seg.bulge != 0:
                    center_point = seg.get_centre_point()
                    centre = self._translate_point(Point(center_point.Z, center_point.X))
                    orientation = "CW"

                    if seg.bulge > 0:
                        orientation = "CCW"

                    self.drawarc(start, end, centre, line_colour, orientation)
                else:
                    self.drawline(start, end, line_colour)

    def _plot_commands(self, gcode, include_rapids):
        """
        Convert an image from supplied geometry
        Valid input: List of type liblathe.command
        """

        for idx, command in enumerate(gcode):

            if idx < len(gcode) - 1:

                movement = command.get_movement()
                if movement not in ["G0", "G1", "G2", "G3"]:
                    continue

                if movement == "G0" and not include_rapids:
                    continue

                params = command.get_params()
                prev_params = gcode[idx - 1].get_params()

                line_colour = self._get_line_colour(movement)

                start = self._translate_point(Point(prev_params['Z'], prev_params['X']))
                end = self._translate_point(Point(params['Z'], params['X']))

                if movement in ["G0", "G1"]:
                    self.drawline(start, end, line_colour)

                if movement in ["G2", "G3"]:
                    centre = self._translate_point(Point(prev_params['Z'] + params['K'], prev_params['X'] + params['I']))
                    orientation = "CW"

                    if movement == "G3":
                        orientation = "CCW"

                    self.drawarc(start, end, centre, line_colour, orientation)

    def drawline(self, start, end, colour):
        """ Add a line element to the drawing """
        self.draw.line([(start.X, start.Y), (end.X, end.Y)], fill=colour, width=self.line_thickness)

    def drawarc(self, start, end, centre, colour, orientation):
        """ Add an arc element to the drawing """

        distance = self._get_distance(centre.X, centre.Y, start.X, start.Y)

        start_angle = self._get_angle(centre.X, centre.Y, start.X, start.Y)
        end_angle = self._get_angle(centre.X, centre.Y, end.X, end.Y)
        boundbox = [(centre.X - distance, centre.Y - distance), (centre.X + distance, centre.Y + distance)]

        if orientation == "CW":
            self.draw.arc(boundbox, end_angle, start_angle, fill=colour, width=self.line_thickness)

        if orientation == "CCW":
            self.draw.arc(boundbox, start_angle, end_angle, fill=colour, width=self.line_thickness)

    def _translate_point(self, point):
        """ convert the supplied point to local coordinates"""
        x = (point.X - self._max_x) * self.scale + self.x_offset
        y = point.Y * self.scale + self.y_offset

        return Point(x, y)

    def backplot(self, input_geometry, include_rapids=True):
        """
        Backplot creates an image from supplied geometry
        Valid input:
        1. List of type liblathe.command
        2. List of type liblathe.segmentgroup
        """
        self._reset_min_max()

        if not isinstance(input_geometry, list):
            print("Backplot input type must be list of type liblathe.command or liblathe.segmentgroup")
            return

        if isinstance(input_geometry[0], Command):
            # process commands
            for command in input_geometry:
                movement = command.get_movement()
                if movement not in ["G0", "G1", "G2", "G3"]:
                    # remove G18
                    input_geometry.remove(command)
                    continue

                params = command.get_params()

                if 'X' in params:
                    self._min_max('y', params['X'])
                if 'Z' in params:
                    self._min_max('x', params['Z'])
        else:
            # process segment groups
            boundbox = input_geometry[-1].boundbox()
            self._min_x = boundbox.z_min
            self._max_x = boundbox.z_max
            self._min_y = boundbox.x_min
            self._max_y = boundbox.x_max

        # size of the image (should be based on the max path point)
        self.scale = self._image_size()
        # define the x and y offset required to translate input geometry to local coordinates - Centre in image for both x and y
        self.x_offset = math.floor(self.image_size[0] - ((self.image_size[0] - (abs(self._max_x - self._min_x) * self.scale)) / 2))
        self.y_offset = math.floor((self.image_size[1] * 0.5))

        if self.transparency:
            img = Image.new('RGBA', self.image_size, (255, 0, 0, 0))
        else:
            img = Image.new('RGB', self.image_size, self.background)

        self.draw = ImageDraw.Draw(img)

        # draw centreline
        cl_y = (self.image_size[1] / 2)
        start = (self.margin * 0.25, cl_y)
        end = (self.image_size[0] - self.margin * 0.25, cl_y)
        self.draw.line([start, end], fill=(252, 226, 5), width=self.line_thickness * 2)

        if isinstance(input_geometry[0], Command):
            self._plot_commands(input_geometry, include_rapids)
        else:
            self._plot_segment_groups(input_geometry)

        # Mirror because its draw flipped.
        if self.mirror_image:
            img = ImageOps.mirror(img)
        elif self.flip_image:
            img = ImageOps.flip(img)
        else:
            img = ImageOps.flip(img)

        if self.transparency:
            img.save(self.file_location + self.image_name + '.png')
        else:
            img.save(self.file_location + self.image_name + self.image_type)

    def _reset_min_max(self):
        self._min_x = 0
        self._min_y = 0
        self._max_x = 0
        self._max_y = 0

    def _min_max(self, coordinate, value):
        # Used to derive the image size based on g code coordinates
        if coordinate == 'x':
            self._min_x = min([value, self._min_x])
            self._max_x = max([value, self._max_x])
        else:
            self._min_y = min([value, self._min_y])
            self._max_y = max([value, self._max_y])

    def _image_size(self):
        # Get the image size
        x = math.ceil(abs(self._min_x - self._max_x))
        y = math.ceil(abs(self._min_y - self._max_y))

        # divide by image size
        x_scale = math.floor((self.image_size[0] - 2 * self.margin) / x)
        y_scale = math.floor((self.image_size[1] * 0.5 - self.margin * 0.5) / y)

        return min([x_scale, y_scale])

    def _get_angle(self, x_start, y_start, x_end, y_end):
        dX = x_end - x_start
        dY = y_end - y_start
        angle = (math.degrees(math.atan2(dY, dX)) + 360) % 360
        return angle

    def _get_distance(self, x_start, y_start, x_end, y_end):
        distance = math.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)
        return distance

    def _get_line_colour(self, value):
        if value == 'G0':
            return self.g0_colour
        elif value == 'G1':
            return self.g1_colour
        elif value == 'G2':
            return self.g2_colour
        elif value == 'G3':
            return self.g3_colour
