#include <limits>

#include "point.h"
#include "utils.h"

Point::Point(float x = 0, float z = 0): x(x), z(z)
{

}

Point::~Point(){}

float Point::distance_to(Point pt){
    // Returns the distance between two points// 
    return sqrt((pt.x- this->x) * (pt.x- this->x) + (pt.z - this->z) * (pt.z - this->z));
}

float Point::angle_to(Point pt){
    // Returns the angle between two points in radians // 
    float dX = this->x - pt.x;
    float dZ = this->z - pt.z;
    float angle = fmod(atan2(dX, dZ) + M_PIf, M_PIf * 2);
    return angle;
}

Point Point::nearest(std::vector<Point> pts){
    // returns nearest point from points //
    Point nearest;
    float distance = std::numeric_limits<float>::infinity(); 
    for (auto pt : pts){
        if (this->distance_to(pt) < distance){
            distance = this->distance_to(pt);
            nearest = pt;
        }
    }
    return nearest;
}

bool Point::is_same(Point pt){
    // Returns True if the coordinates are the same// 
    if (Utils::roundoff(this->x, 5) == Utils::roundoff(pt.x, 5)){
            if (Utils::roundoff(this->z, 5) == Utils::roundoff(pt.z, 5)){
                return true;
            }
    }

    return false;
}

Point Point::sub(Point pt){
    // Returns a point with the difference between this and pt// 
    Point p = Point(this->x - pt.x, this->z - pt.z);
    return p;
}

Point Point::add(Point pt){
    // Returns a point addition between this and pt// 
    Point p = Point(this->x+ pt.x, this->z + pt.z);
    return p;
}

Point Point::multiply(float val){
    // Returns a point multiplication between this and val// 
    Point p = Point(this->x * val, this->z * val);
    return p;
}

Point Point::lerp(Point pt, float t){
    // Returns a point linear interpolation between this and pt
    // t is parameter [0 1] for the distance between this and pt
    // e.g. t = 0.5 will return midpoint between this and pt// 
    Point p = Point(this->x+ (pt.x- this->x) * t, this->z + (pt.z - this->z) * t);
    return p;
}

Point Point::normalise_to(Point pt){
    // returns the normalised direction from this to pt// 
    Point p = pt.sub(*this);
    float m = sqrt(p.x * p.x + p.z * p.z);
    if (m == 0){
        return Point(0.0, 0.0);
    }
    return Point(p.x/ m,  p.z / m);
}

Point Point::rotate(Point center, float angle){
    // Returns a point rotated by angle in radians about center// 
    float x = center.x + (this->x - center.x) * cos(angle) - (this->z - center.z) * sin(angle);
    float z = center.z + (this->x - center.x) * sin(angle) + (this->z - center.z) * cos(angle);
    //float x = this->x* cos(angle) - this->z * sin(angle);
    //float z = this->x* sin(angle) + this->z * cos(angle);
    return Point(x, z);
}

Point Point::mid(Point pt){
    // Returns midpoint between this and pt// 
    float x = (this->x + pt.x) / 2;
    float z = (this->z + pt.z) / 2;
    return Point(x, z);
}

Point Point::project(float angle, float distance){
    // Project the point at angle in radians by distance// 
    float x = Utils::roundoff(this->x + sin(angle) * distance, 5);
    float z = Utils::roundoff(this->z + cos(angle) * distance, 5);
    return Point(x, z);
}
