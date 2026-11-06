#include "boundbox.h"

namespace liblathe
{

    BoundBox::BoundBox(Point pt1, Point pt2)
    {
        // Create axis-aligned bounds from either ordering of two corner points //
        this->XMin = std::min(pt1.X, pt2.X);
        this->ZMin = std::min(pt1.Z, pt2.Z);
        this->XMax = std::max(pt1.X, pt2.X);
        this->ZMax = std::max(pt1.Z, pt2.Z);
    }

    float BoundBox::XLength()
    {
        // Return the extent of the bounds along X //
        return abs(this->XMax - this->XMin);
    }

    float BoundBox::ZLength()
    {
        // Return the extent of the bounds along Z //
        return abs(this->ZMax - this->ZMin);
    }

}
