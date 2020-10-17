from PIL import Image, ImageDraw, ImageOps
import math
import os


class Plot:
    def __init__(self):
        self.background = (168, 168, 168)
        self.transparency = False
        self.fileLocation = ''
        self.imageName = 'image1'
        self.imageType = '.jpg'
        self.imageSize = (1920, 1080)
        self.g0Color = (256, 0, 0)
        self.g1Color = (0, 256, 0)
        self.g2Color = (0, 256, 0)
        self.g3Color = (0, 256, 0)
        self.lineThickness = 2

        self.__min_x = 500000
        self.__min_y = 500000
        self.__max_x = -500000
        self.__max_y = -500000

    def set_file_path(self, path):
        """Specify the location to save the plotted image"""
        if os.path.exists(path):
            self.fileLocation = path
        else:
            raise Warning('Given file path does not exist!')

    def set_transparency(self):
        """Set transparency on/off"""
        self.transparency = not self.transparency

    def set_background_color(self, color):
        """"Set background color of image"""
        if isinstance(color, tuple) and len(color) == 3:
            try:
                self.background = color
            except Exception:
                raise Warning('Unknown color! Color is RGB. For example (255, 255, 255)')

    def set_path_color(self, g_number, color):
        """Set the colour of g path. For example G0, (255,255,255)"""
        if isinstance(color, tuple) and len(color) == 3:
            try:
                if g_number.upper().startswith('G0'):
                    self.g0Color = color
                elif g_number.upper().startswith('G1'):
                    self.g1Color = color
                elif g_number.upper().startswith('G2'):
                    self.g2Color = color
                elif g_number.upper().startswith('G3'):
                    self.g3Color = color
            except Exception:
                raise Warning('Unknown value! Please use for example G0, (255,255,255)')
        else:
            raise Warning('Unknown color! Color is RGB. For example (255, 255, 255)')

    def set_line_thickness(self, value):
        """Set the line thick to be drawn. Must be an integer value"""
        if isinstance(value, int):
            self.lineThickness = value
        else:
            raise Warning('Unknown thickness value! Thickness must be an integer!')

    def set_image_details(self, imageName='image1', imageType='.jpg', imageSize=(1920, 1080)):
        """"Set image details. Image name, image type (.jpg, .png) and image size (1080, 720)"""
        self.imageName = imageName
        self.imageSize = imageSize

        if not imageType.startswith('.'):
            self.imageType = '.' + imageType
        else:
            self.imageType = imageType

    def backplot(self, gcode):
        """Backplot creates an image from supplied LibLathe g code"""
        code = []
        self.__reset_min_max()

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
                            self.__min_max('x', float(i[1:]))

                        elif i[0].upper() == 'Y':
                            continue

                        elif i[0].upper() == 'Z':
                            col['z'] = float(i[1:])
                            self.__min_max('y', float(i[1:]))

                        elif i[0].upper() == 'F':
                            continue

                        else:
                            print(line)
                            raise Warning('Unknown character!')
                else:
                    continue

                code.append(col)
        self.__draw_image(code)

    def __reset_min_max(self):
        self.__min_x = 0
        self.__min_y = 0
        self.__max_x = 0
        self.__max_y = 0

    def __min_max(self, coordinate, value):
        # Used to derive the image size based on g code coordinates
        if coordinate == 'x':
            self.__min_x = min([value, self.__min_x])
            self.__max_x = max([value, self.__max_x])
        else:
            self.__min_y = min([value, self.__min_y])
            self.__max_y = max([value, self.__max_y])

    def __image_size(self):
        # Get the image size
        x = math.ceil(abs(self.__min_x - self.__max_x))
        y = math.ceil(abs(self.__min_y - self.__max_y))

        # divide by image size
        x_scale = math.floor(self.imageSize[0] / x)
        y_scale = math.floor(self.imageSize[1] / y)

        # scale up
        self.imageSize = ((x * x_scale) + 50, (y * y_scale) + 50)

        return min([x_scale, y_scale])

    def __draw_image(self, code):
        # size of the image (should be based on the max path point)
        scale = self.__image_size()

        if self.transparency:
            img = Image.new('RGBA', self.imageSize, (255, 0, 0, 0))
        else:
            img = Image.new('RGB', self.imageSize, self.background)

        draw = ImageDraw.Draw(img)

        i = 0
        x = 1
        while i <= (len(code) - 1):
            line_color = self.__get_line_color(code[i]['g'][0])

            # / 2 to draw from the center of the image
            # - 25 to offset the draw point from the edge of the image
            x_start = (self.imageSize[0] / 2) + (code[i]['z'] * scale) - 25
            y_start = self.imageSize[1] + (code[i]['x'] * scale) - 25
            x_end = (self.imageSize[0] / 2) + (code[x]['z'] * scale) - 25
            y_end = self.imageSize[1] + (code[x]['x'] * scale) - 25

            draw.line((x_start, y_start, x_end, y_end), fill=line_color, width=self.lineThickness)
            i += 1
            if x != (len(code) - 1):
                x += 1

        # Mirror because its draw flipped.
        img = ImageOps.flip(img)
        if self.transparency:
            img.save(self.fileLocation + self.imageName + '.png')
        else:
            img.save(self.fileLocation + self.imageName + self.imageType)

    def __get_line_color(self, value):
        if value == 'G0':
            return self.g0Color
        elif value == 'G1':
            return self.g1Color
        elif value == 'G2':
            return self.g2Color
        elif value == 'G3':
            return self.g3Color