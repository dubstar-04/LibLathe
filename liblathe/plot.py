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
        self.g0Colour = (256, 0, 0)
        self.g1Colour = (0, 256, 0)
        self.g2Colour = (0, 256, 0)
        self.g3Colour = (0, 256, 0)
        self.lineThickness = 2
        self.rapidOnly = False
        self.cutsOnly = False
        self.specifiedPlot = ''
        self.specifiedPlotColour = (0, 256, 0)
        self.mirrorImage = False
        self.flipImage = True
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
                    self.g0Colour = colour
                elif g_number.upper().startswith('G1'):
                    self.g1Colour = colour
                elif g_number.upper().startswith('G2'):
                    self.g2Colour = colour
                elif g_number.upper().startswith('G3'):
                    self.g3Colour = colour
            except Exception:
                raise Warning('Unknown value! Please use for example G0, (255,255,255)')
        else:
            raise Warning('Unknown colour! Colour is RGB. For example (255, 255, 255)')

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
        self.mirrorImage = not self.mirrorImage
        self.flipImage = False

    def flip_image_vertical(self):
        """Flip the image vertically(top to bottom). Turns On/Off"""
        self.flipImage = not self.flipImage
        self.mirrorImage = False

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

                        elif i[0].upper() == 'I':
                            col['i'] = float(i[1:])

                        elif i[0].upper() == 'K':
                            col['k'] = float(i[1:])

                        elif i[0].upper() == 'Z':
                            col['z'] = float(i[1:])
                            self.__min_max('y', float(i[1:]))

                        elif i[0].upper() == 'F':
                            continue

                        else:
                            print(command)
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
            line_colour = self.__get_line_colour(code[i]['g'][0])

            # / 2 to draw from the center of the image
            # - 25 to offset the draw point from the edge of the image
            x_start = (self.imageSize[0] / 2) + (code[i]['z'] * scale) - 25
            y_start = self.imageSize[1] + (code[i]['x'] * scale) - 25
            x_end = (self.imageSize[0] / 2) + (code[x]['z'] * scale) - 25
            y_end = self.imageSize[1] + (code[x]['x'] * scale) - 25

            if not self.rapidOnly and not self.cutsOnly and self.specifiedPlot == '':
                draw.line((x_start, y_start, x_end, y_end), fill=line_colour, width=self.lineThickness)
            elif self.specifiedPlot != '':
                if code[x]['g'][0] == self.specifiedPlot:
                    draw.line((x_start, y_start, x_end, y_end), fill=self.specifiedPlotColour, width=self.lineThickness)
            else:
                if self.rapidOnly and code[x]['g'][0] == 'G0':
                    draw.line((x_start, y_start, x_end, y_end), fill=self.g0Colour, width=self.lineThickness)
                
            if not self.rapidOnly and not self.cutsOnly:
                draw.line((x_start, y_start, x_end, y_end), fill=line_colour, width=self.lineThickness)
            elif self.specifiedPlot != '':
                if code[x]['g'][0] == self.specifiedPlot:
                    draw.line((x_start, y_start, x_end, y_end), fill=self.specifiedPlotColour, width=self.lineThickness)
            else:
                if self.rapidOnly and code[x]['g'][0] == 'G0':
                    draw.line((x_start, y_start, x_end, y_end), fill=self.g0Colour, width=self.lineThickness)
                elif self.cutsOnly and code[x]['g'][0] == 'G1':
                    draw.line((x_start, y_start, x_end, y_end), fill=self.g1Colour, width=self.lineThickness)

            i += 1
            if x != (len(code) - 1):
                x += 1

        # Mirror because its draw flipped.
        if self.mirrorImage:
            img = ImageOps.mirror(img)
        elif self.flipImage:
            img = ImageOps.flip(img)
        else:
            img = ImageOps.flip(img)

        if self.transparency:
            img.save(self.fileLocation + self.imageName + '.png')
        else:
            img.save(self.fileLocation + self.imageName + self.imageType)

    def __get_line_colour(self, value):
        if value == 'G0':
            return self.g0Colour
        elif value == 'G1':
            return self.g1Colour
        elif value == 'G2':
            return self.g2Colour
        elif value == 'G3':
            return self.g3Colour
