#ifndef BoundBox_H
#define BoundBox_H

#include "point.h"

namespace liblathe
{

    class BoundBox
    {
    public:
        BoundBox(Point pt1, Point pt2);
        // Destroy the axis-aligned bounds //
        ~BoundBox() {};
        float XLength();
        float ZLength();

        float XMin;
        float ZMin;
        float XMax;
        float ZMax;
    };

}

#endif
