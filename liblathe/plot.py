from PIL import Image, ImageDraw, ImageOps
import math
import os


class Plot:
    def _init_(self):
        self.background = (168, 168, 168)
        self.transparency = False
        self.file_location = ''
        self.image_name = 'image1'
        self.image_type = '.jpg'
        self.imageSize = (1920, 1080)
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

    def set_image_details(self, image_name='image1', image_type='.jpg', imageSize=(1920, 1080)):
        """"Set image details. Image name, image type (.jpg, .png) and image size (1080, 720)"""
        self.image_name = image_name
        self.imageSize = imageSize

        if not image_type.startswith('.'):
            self.image_type = '.' + image_type
        else:
            self.image_type = image_type

    def backplot(self, gcode):
        """Backplot creates an image from supplied LibLathe g code"""
        code = []
        self._reset_min_max()

        for line in gcode:
            for command in line:
                command = command.to_string()

                if command == '':
                    continue

                elif command.startswith('G'):
                    col = {}

                    commands = command.split(' ')
                    if command[0:] == 'G18':
                        continue

                    col['g'] = commands[0:1]

                    for i in commands[1:]:
                        if len(commands) <= 1:
                            continue

                        elif i[0].upper() == 'X':
                            col['x'] = float(i[1:])
                            self._min_max('x', float(i[1:]))

                        elif i[0].upper() == 'Y':
                            continue

                        elif i[0].upper() == 'Z':
                            col['z'] = float(i[1:])
                            self._min_max('y', float(i[1:]))

                        elif i[0].upper() == 'F':
                            continue

                        else:
                            print(line)
                            raise Warning('Unknown character!')
                else:
                    continue

                code.append(col)
        self._draw_image(code)

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
        x_scale = math.floor(self.imageSize[0] / x)
        y_scale = math.floor(self.imageSize[1] / y)

        # scale up
        self.imageSize = ((x * x_scale) + 50, (y * y_scale) + 50)

        return min([x_scale, y_scale])

    def _draw_image(self, code):
        # size of the image (should be based on the max path point)
        scale = self._image_size()

        if self.transparency:
            img = Image.new('RGBA', self.imageSize, (255, 0, 0, 0))
        else:
            img = Image.new('RGB', self.imageSize, self.background)

        draw = ImageDraw.Draw(img)

        i = 0
        x = 1
        while i <= (len(code) - 1):
            line_colour = self._get_line_colour(code[i]['g'][0])

            # / 2 to draw from the center of the image
            # - 25 to offset the draw point from the edge of the image
            x_start = (self.imageSize[0] / 2) + (code[i]['z'] * scale) - 25
            y_start = self.imageSize[1] + (code[i]['x'] * scale) - 25
            x_end = (self.imageSize[0] / 2) + (code[x]['z'] * scale) - 25
            y_end = self.imageSize[1] + (code[x]['x'] * scale) - 25

            draw.line((x_start, y_start, x_end, y_end), fill=line_colour, width=self.line_thickness)
            i += 1
            if x != (len(code) - 1):
                x += 1

        # Mirror because its draw flipped.
        img = ImageOps.flip(img)
        if self.transparency:
            img.save(self.file_location + self.image_name + '.png')
        else:
            img.save(self.file_location + self.image_name + self.image_type)

    def _get_line_colour(self, value):
        if value == 'G0':
            return self.g0_colour
        elif value == 'G1':
            return self.g1_colour
        elif value == 'G2':
            return self.g2_colour
        elif value == 'G3':
            return self.g3_colour
