#ifndef BoundBox_H
#define BoundBox_H

#include "point.h"

class BoundBox
{
    public:
        BoundBox(Point pt1, Point pt2);
        ~BoundBox(){};
        float x_length();
        float z_length();

        float x_min;
        float z_min;
        float x_max;
        float z_max;
};

#endif