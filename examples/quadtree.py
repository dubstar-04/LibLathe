# Add LibLathe is in the Python Path
import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)

from liblathe.base.quadtree import Quadtree, Point, Node

start_time = time.time()

def quadtree_test():
    
    qt = Quadtree()

    # add shape points
    qt.add_point(0, 10)
    qt.add_point(2.36, 9.72)
    qt.add_point(4.58, 8.89)
    qt.add_point(6.55, 7.56)
    qt.add_point(8.15, 5.80)
    qt.add_point(9.28, 3.72)
    qt.add_point(9.9, 1.42)
    qt.add_point(9.95, -0.95)
    qt.add_point(9.45, -3.27)
    qt.add_point(8.41, -5.41)
    qt.add_point(6.90, -7.24)
    qt.add_point(5, -9)
    qt.add_point(9.5, -15.85)
    qt.add_point(5.4, -22)
    qt.add_point(4.03, -22.68)
    qt.add_point(3.01, -23.81)
    qt.add_point(2.45, -25.23)
    qt.add_point(2.45, -26.76)
    qt.add_point(3.00, -28.18)
    qt.add_point(4.02, -29.31)
    qt.add_point(5.4, -30)
    qt.add_point(5.4, -40)
    qt.add_point(13, -45)
    qt.add_point(13, -48)
    qt.add_point(0, -48)

    print('pnt count', qt.point_count())

    # Define stock bounds
    #stockPt1 = Point(0, 0, 25)
    #stockPt2 = Point(15, 0, -50)
    #StockBoundingBox = BoundBox(stockPt1, stockPt2)

    # create a 2D Quadtree / SDF for the part geometry
    x_min = 0
    x_max = 25

    z_min = -60
    z_max = 25

    print('limits', x_min, x_max, z_min, z_max)

    height = abs(x_max - x_min)
    width = abs(z_max - z_min)

    center = Point( height / 2, z_min + width / 2)


    qt.add_base_node(center, width, height)

    sdf_time = time.time()
    print("SDF time: ", sdf_time - start_time)

    target = 0.25
    offset = qt.get_offset(target)
    print('points:', len(offset))

    offset_time = time.time()
    print("offset_time: ", offset_time - start_time)

    #nodes = qt.get_nodes()
    #print('nodes:', len(nodes))
   

    '''
    p = Point(100, 101)
    s = Point(12, 13)
    e = Point(14, 15)
    print('point', p.x, p.z)
    c = sdf.closest(p, s, e)
    print('closest', c.x, c.z)
    '''


    show = True
    if show:
        # width = len(sdf_out)
        # height = len(sdf_out[0])

        print('size', width, height)
        
        # creating new Image object
        img = Image.new("RGB", (width * 10, height * 10))

        # create rectangle image
        img1 = ImageDraw.Draw(img)

        '''
        target = 0.26
        threshold = 0.01
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
        '''
        
        for pt in offset:
            x = pt.x * 10
            z = (pt.z + 60)* 10
            shape = [(z, x), (z + 1, x + 1)]  
            img1.rectangle(shape, fill ="#fc0303")
        
        if False:
            for node in nodes:
                tz = ((node.center.z - node.width / 2) + 60) * 10
                tx = (node.center.x - node.height / 2) * 10
                shape = [(tz, tx), (tz + node.width * 10, tx + node.height * 10)]
                colour = "#ffff33"
                if node.sdv < 0:
                    colour = "#00ffff"
                img1.rectangle(shape, outline = colour)
                '''
                x = node.center.x * 10
                z = (node.center.z + 60) * 10
                point = [(z, x), (z + 1, x + 1)]  
                img1.rectangle(point, fill ="#fc0303")
                '''

        end_time = time.time()

        print("Elapsed time: ", end_time - start_time) 

        img.show()
    


quadtree_test()
