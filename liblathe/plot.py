import math
import os

from PIL import Image, ImageDraw, ImageOps


class Plot:
    def __init__(self):
        self.background = (168, 168, 168)
        self.transparency = False
        self.file_location = ''
        self.image_name = 'image1'
        self.image_type = '.jpg'
        self.image_size = (1920, 1080)
        self.mirror_image = False
        self.flip_image = True
        self.g0_colour = (256, 0, 0)
        self.g1_colour = (0, 256, 0)
        self.g2_colour = (0, 256, 0)
        self.g3_colour = (0, 256, 0)
        self.line_thickness = 2

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

    def set_line_thickness(self, value):
        """Set the line thick to be drawn. Must be an integer value"""
        if isinstance(value, int):
            self.line_thickness = value
        else:
            raise Warning('Unknown thickness value! Thickness must be an integer!')

    def set_image_details(self, image_name='image1', image_type='.jpg', image_size=(1920, 1080)):
        """"Set image details. Image name, image type (.jpg, .png) and image size (1080, 720)"""
        self.image_name = image_name
        self.image_size = image_size

        if not image_type.startswith('.'):
            self.image_type = '.' + image_type
        else:
            self.image_type = image_type

    def draw_rapids_only(self):
        """Draw rapid only on/off"""
        self.rapidOnly = not self.rapidOnly
        self.cutsOnly = False
        self.specifiedPlot = ''
        self.cutsOnly = ''

    def draw_cuts_only(self):
        """Draw cuts only on/off"""
        self.cutsOnly = not self.cutsOnly
        self.rapidOnly = False
        self.specifiedPlot = ''
        self.cutsOnly = ''

    def draw_specified(self, gcode, colour):
        """Draws only specified cut. For example G2"""
        self.specifiedPlot = gcode
        if isinstance(colour, tuple) and len(colour) == 3:
            try:
                self.specifiedPlotColour = colour
            except Exception:
                raise Warning('Unknown colour! Colour is RGB. For example (255, 255, 255)')
        self.cutsOnly = False
        self.rapidOnly = False

    def flip_image_horizontal(self):
        """Flip image horizontally(left to right).Turns On/Off"""
        self.mirror_image = not self.mirror_image
        self.flip_image = False

    def flip_image_vertical(self):
        """Flip the image vertically(top to bottom). Turns On/Off"""
        self.flip_image = not self.flip_image
        self.mirror_image = False

    def backplot(self, gcode):
        """Backplot creates an image from supplied LibLathe g code"""

        self._reset_min_max()

        for command in gcode:
            # for command in line:

            movement = command.get_movement()
            if movement not in ["G0", "G1", "G2", "G3"]:
                # remove G18
                gcode.remove(command)
                continue

            params = command.get_params()

            if 'X' in params:
                self._min_max('y', params['X'])
            if 'Z' in params:
                self._min_max('x', params['Z'])

        self._draw_image(gcode)

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
        x_scale = math.floor(self.image_size[0] / x)
        y_scale = math.floor(self.image_size[1] / y)

        # scale up
        self.image_size = ((x * x_scale) + 50, (y * y_scale) + 50)

        return min([x_scale, y_scale])

    def _draw_image(self, gcode):
        # size of the image (should be based on the max path point)
        scale = self._image_size()

        if self.transparency:
            img = Image.new('RGBA', self.image_size, (255, 0, 0, 0))
        else:
            img = Image.new('RGB', self.image_size, self.background)

        draw = ImageDraw.Draw(img)

        for idx, command in enumerate(gcode):
            print('line:', command.movement, command.params)
            # for command in line:

            if idx < len(gcode) - 1:

                movement = command.get_movement()
                if movement not in ["G0", "G1", "G2", "G3"]:
                    continue

                params = command.get_params()
                prev_params = gcode[idx - 1].get_params()

                line_colour = self._get_line_colour(movement)

                x_start = self.image_size[0] / 2 + prev_params['Z'] * scale - 25
                y_start = self.image_size[1] + prev_params['X'] * scale - 25
                x_end = self.image_size[0] / 2 + params['Z'] * scale - 25
                y_end = self.image_size[1] + params['X'] * scale - 25

                if movement in ["G0", "G1"]:
                    draw.line([(x_start, y_start), (x_end, y_end)], fill=line_colour, width=self.line_thickness)

                if movement in ["G2", "G3"]:
                    x_centre = (self.image_size[0] / 2 + (prev_params['Z'] + params['K']) * scale - 25)
                    y_centre = (self.image_size[1] + (prev_params['X'] + params['I']) * scale - 25)

                    distance = self._get_distance(x_centre, y_centre, x_start, y_start)

                    start_angle = self._get_angle(x_centre, y_centre, x_start, y_start)
                    end_angle = self._get_angle(x_centre, y_centre, x_end, y_end)
                    boundbox = [(x_centre - distance, y_centre - distance), (x_centre + distance, y_centre + distance)]
                    if movement == "G2":
                        draw.arc(boundbox, end_angle, start_angle, fill=line_colour, width=self.line_thickness)

                    if movement == "G3":
                        draw.arc(boundbox, start_angle, end_angle, fill=line_colour, width=self.line_thickness)

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
