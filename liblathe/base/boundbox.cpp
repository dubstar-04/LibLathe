#include "boundbox.h"

BoundBox::BoundBox(Point pt1, Point pt2){

    this->x_min = std::min(pt1.x, pt2.x);
    this->z_min = std::min(pt1.z, pt2.z);
    this->x_max = std::max(pt1.x, pt2.x);
    this->z_max = std::max(pt1.z, pt2.z);
}

float BoundBox::x_length(){
    // Return length in x direction// 
    return abs(this->x_max - this->x_min);
}

float BoundBox::z_length(){
    // Return length in z direction// 
    return abs(this->z_max - this->z_min);
}
