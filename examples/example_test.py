# Add LibLathe is in the Python Path
import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.sdf import add, SDF, Point

start_time = time.time()

def sdf_test():
    sdf = SDF()

    # add shape points
    sdf.add_point(0, 10)
    sdf.add_point(2.36, 9.72)
    sdf.add_point(4.58, 8.89)
    sdf.add_point(6.55, 7.56)
    sdf.add_point(8.15, 5.80)
    sdf.add_point(9.28, 3.72)
    sdf.add_point(9.9, 1.42)
    sdf.add_point(9.95, -0.95)
    sdf.add_point(9.45, -3.27)
    sdf.add_point(8.41, -5.41)
    sdf.add_point(6.90, -7.24)
    sdf.add_point(5, -9)
    sdf.add_point(9.5, -15.85)
    sdf.add_point(5.4, -22)
    sdf.add_point(4.03, -22.68)
    sdf.add_point(3.01, -23.81)
    sdf.add_point(2.45, -25.23)
    sdf.add_point(2.45, -26.76)
    sdf.add_point(3.00, -28.18)
    sdf.add_point(4.02, -29.31)
    sdf.add_point(5.4, -30)
    sdf.add_point(5.4, -40)
    sdf.add_point(13, -45)
    sdf.add_point(13, -48)
    sdf.add_point(0, -48)

    print('pnt count', sdf.point_count())

    sdf_out = sdf.generate()

    sdf_time = time.time()

    print("SDF time: ", sdf_time - start_time)

    # print(sdf_out)

    '''
    p = Point(100, 101)
    s = Point(12, 13)
    e = Point(14, 15)
    print('point', p.x, p.z)
    c = sdf.closest(p, s, e)
    print('closest', c.x, c.z)
    '''

    print(type(sdf_out), type(sdf_out[0]))

    show = False
    if show:
        width = len(sdf_out)
        height = len(sdf_out[0])

        print('size', width, height)
        
        # creating new Image object
        img = Image.new("RGB", (width, height))

        # create rectangle image
        img1 = ImageDraw.Draw(img)

        target = 0.1
        threshold = 0.005 * 0.5
        sdf_out.reverse()
        for z, column in enumerate(sdf_out):
            for x, row in enumerate(column):
                #print(x, z)
                value = sdf_out[z][x]
                #print(value)
                shape = [(z, x), (z + 1, x + 1)] 
                colour = '#' + '000000'

                if value > 0:
                    colour = '#{:02x}{:02x}{:02x}'.format(255, int(value * 10), int(value * 10))
                    for i in range(0, 200, 20):
                        if value < (target * i) + threshold and value > (target * i) - threshold:
                            colour = '#' + '000000'

                if value < -1 + threshold and value > -1 - threshold:
                    colour = '#' + 'ffffff'


                img1.rectangle(shape, fill = colour)


        end_time = time.time()

        print("Elapsed time: ", end_time - start_time) 

        img.show()
    


sdf_test()
