#include <cmath>
#include <limits>

#include "point.h"
#include "utils.h"

namespace liblathe
{

    Point::Point(float x, float z) : X(x), Z(z)
    {
        // Create a point with the supplied X and Z coordinates //
    }

    Point::~Point()
    {
        // Destroy the point //
    }

    float Point::distanceTo(Point pt)
    {
        // Return the Euclidean distance to another point //
        return sqrt((pt.X - this->X) * (pt.X - this->X) + (pt.Z - this->Z) * (pt.Z - this->Z));
    }

    float Point::angleTo(Point pt)
    {
        // Return the direction angle to another point in radians //
        // Work in double: float atan2 and M_PIf round differently across platforms //
        constexpr double pi = 3.14159265358979323846;
        const double dX = double(this->X) - pt.X;
        const double dZ = double(this->Z) - pt.Z;
        return float(std::fmod(std::atan2(-dX, dZ) + pi, 2 * pi));
    }

    Point Point::nearest(std::vector<Point> pts)
    {
        // Return the nearest supplied point, or the origin if none are supplied //
        Point nearest;
        float distance = std::numeric_limits<float>::infinity();
        for (auto pt : pts)
        {
            if (this->distanceTo(pt) < distance)
            {
                distance = this->distanceTo(pt);
                nearest = pt;
            }
        }
        return nearest;
    }

    bool Point::isSame(Point pt)
    {
        // Compare coordinates rounded to five decimal places //
        if (Utils::roundoff(this->X, 5) == Utils::roundoff(pt.X, 5))
        {
            if (Utils::roundoff(this->Z, 5) == Utils::roundoff(pt.Z, 5))
            {
                return true;
            }
        }

        return false;
    }

    Point Point::sub(Point pt)
    {
        // Return the coordinate difference from another point //
        Point p = Point(this->X - pt.X, this->Z - pt.Z);
        return p;
    }

    Point Point::add(Point pt)
    {
        // Return the coordinate sum with another point //
        Point p = Point(this->X + pt.X, this->Z + pt.Z);
        return p;
    }

    Point Point::multiply(float val)
    {
        // Return the coordinates scaled by the supplied value //
        Point p = Point(this->X * val, this->Z * val);
        return p;
    }

    Point Point::lerp(Point pt, float t)
    {
        // Interpolate between this point and another using parameter t //
        // t is parameter [0 1] for the distance between this and pt
        // e.g. t = 0.5 will return midpoint between this and pt//
        Point p = Point(this->X + (pt.X - this->X) * t, this->Z + (pt.Z - this->Z) * t);
        return p;
    }

    Point Point::normaliseTo(Point pt)
    {
        // Return the unit direction to another point, or zero for coincident points //
        Point p = pt.sub(*this);
        float m = sqrt(p.X * p.X + p.Z * p.Z);
        if (m == 0)
        {
            return Point(0.0, 0.0);
        }
        return Point(p.X / m, p.Z / m);
    }

    Point Point::rotate(Point center, float angle)
    {
        // Rotate the point about the supplied centre by an angle in radians //
        float x = center.X + (this->X - center.X) * cos(angle) - (this->Z - center.Z) * sin(angle);
        float z = center.Z + (this->X - center.X) * sin(angle) + (this->Z - center.Z) * cos(angle);
        // float x = this->X* cos(angle) - this->Z * sin(angle);
        // float z = this->X* sin(angle) + this->Z * cos(angle);
        return Point(x, z);
    }

    Point Point::mid(Point pt)
    {
        // Return the midpoint between this point and another //
        float x = (this->X + pt.X) / 2;
        float z = (this->Z + pt.Z) / 2;
        return Point(x, z);
    }

    Point Point::project(float angle, float distance)
    {
        // Project by a distance at an angle in radians, rounding coordinates to five decimals //
        float x = Utils::roundoff(this->X - sin(angle) * distance, 5);
        float z = Utils::roundoff(this->Z + cos(angle) * distance, 5);
        return Point(x, z);
    }

}
