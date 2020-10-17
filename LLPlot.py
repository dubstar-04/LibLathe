from PIL import Image, ImageDraw, ImageOps


class Plot:
    def __init__(self):
        self.background = (168, 168, 168)
        self.imageName = 'image1'
        self.imageType = '.jpg'
        self.imagesize = (1080, 720)

        self.__min_x = 0
        self.__min_y = 0
        self.__max_x = 0
        self.__max_y = 0

    def set_background_color(self, color):
        """"Set background color of image"""
        if isinstance(color, array) and len(color) == 3:
            try:
                self.background = color
            except Exception:
                raise Warning('Unknown color! Color is RGB. For example (255, 255, 255)')

    def set_image_details(self, imageName='image1', imageType='.jpg'):
        """"Set image details. Image name and image type (.jpg, .png)"""
        self.imageName = imageName
        if not imageType.startswith('.'):
            self.imageType = '.' + imageType
        else:
            self.imageType = imageType

    def backplot(self, gcode):
        """Backplot creates an image from supplied LibLathe g code"""

        code = []

        self.__min_x = 0
        self.__min_y = 0
        self.__max_x = 0
        self.__max_y = 0

        # read each line
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
                            self.__image_size('x', float(i[1:]))

                        elif i[0].upper() == 'Y':
                            continue

                        elif i[0].upper() == 'Z':
                            col['z'] = float(i[1:])
                            self.__image_size('y', float(i[1:]))

                        elif i[0].upper() == 'F':
                            continue

                        else:
                            print(line)
                            raise Warning('Unknown character!')
                else:
                    continue

                code.append(col)
        self.__draw_image(code)

    def __image_size(self, coordinate, value):
        if coordinate == 'x':
            self.__min_x = min([value, self.__min_x])
            self.__max_x = max([value, self.__max_x])
        else:
            self.__min_y = min([value, self.__min_y])
            self.__max_y = max([value, self.__max_y])

    def __draw_image(self, code):
        # ---------------------------------------------------------------------
        # Draw the image
        # ---------------------------------------------------------------------
        # size of the image (should be based on the max path point)
        size = 1500, 800
        img = Image.new('RGB', size, self.background)
        draw = ImageDraw.Draw(img)

        i = 0
        x = 1
        while i <= (len(code) - 1):

            fill = (0, 256, 0)
            if code[i]['g'][0] == 'G0':
                fill = (256, 0, 0)

            # / 2 to draw from the center of the image
            # - 50 to offset the draw point from the edge of the image
            x_start = (size[0] / 2) + (code[i]['z'] * 30)
            y_start = size[1] + (code[i]['x'] * 30) - 50
            x_end = (size[0] / 2) + (code[x]['z'] * 30)
            y_end = size[1] + (code[x]['x'] * 30) - 50

            draw.line((x_start, y_start, x_end, y_end), fill=fill)
            i += 1
            if x != (len(code) - 1):
                x += 1

        # Mirror because its draw flipped.
        img = ImageOps.flip(img)
        img.save(self.imageName + self.imageType)
