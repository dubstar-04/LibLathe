from PIL import Image, ImageDraw, ImageOps
import sys


class Plot:
    def __init__(self, gcode):
        self.gcode = gcode

    def backplot(self):
        # ---------------------------------------------------------------------
        # Read G Code
        # ---------------------------------------------------------------------
        # inputFile = 'profile.gcode'
        # file = open(inputFile, 'r')
        code = []

        # read each line
        for line in self.gcode:
            for command in line:
                command = command.to_string()

                if command == '':
                    continue

                if command.startswith('G'):
                    col = {}

                    commands = command.split(' ')
                    if line[0:] == 'G18':
                        continue

                    col['g'] = commands[0:1]

                    for i in commands[1:]:

                        if len(commands) <= 1:
                            print(i)
                            continue

                        elif i[0] == 'X':
                            col['x'] = float(i[1:])

                        elif i[0] == 'Y':
                            continue

                        elif i[0] == 'Z':
                            col['z'] = float(i[1:])

                        elif i[0] == 'F':
                            # can do something with speeds here in future
                            continue

                        else:
                            print(line)
                            raise Warning('Unknown character!')

                        code.append(col)
        code.append(col)

        # ---------------------------------------------------------------------
        # Draw the image
        # ---------------------------------------------------------------------
        # size of the image (should be based on the max path point)
        size = 1500, 800
        img = Image.new('RGB', size, (168, 168, 168))
        data = img.load()
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
        img.save('image1.jpg')
