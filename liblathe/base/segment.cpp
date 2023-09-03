#include <iostream>
#include "segment.h"

Segment::Segment(Point start, Point end) : start(start), end(end)
{
}

Segment::Segment(Point start, Point end, float bulge = 0) : start(start), end(end), bulge(bulge)
{
}

float Segment::get_angle()
{
    // Returns the included angle between the start && end points in radians//
    // TODO: Is this supposed to return 0 to 2 * M_PIf?

    if (this->bulge == 0)
    {
        return M_PIf;
    }

    return atan(abs(this->bulge)) * 4;
}

void Segment::set_bulge(float angle)
{
    /*
    Sets the bulge of the arc (tan(angle/4))
    Negative bulge = clockwise
    Positive bulge = anticlockwise
    angle in radians
    */

    this->bulge = tan(angle / 4);
}

Point Segment::get_centre_point()
{
    // Returns the centre point of the arc //
    Point midp = this->start.mid(this->end);
    if (this->bulge == 0)
    {
        return midp;
    }

    float a = this->get_apothem();
    //  check if (the center point is inverted. i.e. at 180 it goes inside the arc
    if (this->get_angle() > M_PIf)
    {
        a = -a;
    }

    Point centre_pt = midp.project(this->get_rotation() + M_PI_2f, a);
    if (this->bulge > 0)
    {
        centre_pt = midp.project(this->get_rotation() - M_PI_2f, a);
    }

    return centre_pt;
}

float Segment::get_radius()
{
    // Return the radius of the arc //

    if (this->bulge == 0)
    {
        return 0.0;
    }

    float rad = this->get_length() * (1 + pow(this->bulge, 2)) / (4 * abs(this->bulge));
    return rad;
}

float Segment::get_rotation()
{
    // returns the rotation of the segment//
    return this->start.angle_to(this->end);
}

BoundBox Segment::get_boundbox()
{
    // returns the segments boundingbox //

    Point topLeft, bottomRight;

    if (this->bulge == 0)
    {
        topLeft = this->start;
        bottomRight = this->end;
    } else {
        float startAngle = this->get_centre_point().angle_to(this->start);
        float endAngle = this->get_centre_point().angle_to(this->end);

        bool cross0 = this->crossesAxis(startAngle, endAngle, 0);
        bool cross90 = this->crossesAxis(startAngle, endAngle, M_PI_2f);
        bool cross180 = this->crossesAxis(startAngle, endAngle, M_PIf);
        bool cross270 = this->crossesAxis(startAngle, endAngle, M_PIf * 1.5);

        //  if (the arc crosses the axis the min or max is where the arc intersects the axis
        //  otherwise max/min is the arc endpoint
        float zmax = cross0 ? this->get_centre_point().z + this->get_radius() : std::max(this->start.z, this->end.z);
        float xmin = cross90 ? this->get_centre_point().x - this->get_radius() : std::min(this->start.x, this->end.x);
        float zmin = cross180 ? this->get_centre_point().z - this->get_radius() : std::min(this->start.z, this->end.z);
        float xmax = cross270 ? this->get_centre_point().x + this->get_radius() : std::max(this->start.x, this->end.x);

        topLeft = Point(xmin, zmin);
        bottomRight = Point(xmax, zmax);
    }

    return BoundBox(topLeft, bottomRight);
}

bool Segment::crossesAxis(float startAngle, float endAngle, float axisAngle)
{
    // check of the axis angle is between the start and end angles
    // i.e. the arc crosses the axis

    float circle = M_PIf * 2;
    float referenceStartAngle = fmod((startAngle - axisAngle + circle), circle);
    float referenceEndAngle = fmod((endAngle - axisAngle + circle), circle);

    //  if refStartAngle > refEndAngle then the arc crosses the axis
    bool crosses = referenceStartAngle <= referenceEndAngle;

    if (this->bulge < 0)
    {
        //  if refStartAngle < refEndAngle then the arc crosses the axis
        crosses = referenceStartAngle >= referenceEndAngle;
    }

    return crosses;
}

float Segment::get_length()
{
    // Returns the distance between the start && end points //
    //  TODO: Arc length should be the true length not the distance between the start && endpoints?
    return this->start.distance_to(this->end);
}

float Segment::get_sagitta()
{
    // Returns the arc height, typically referred to as the sagitta //
    return this->get_length() / 2 * this->bulge;
}

float Segment::get_apothem()
{
    // Returns apothem. distance from arc center to c||d midpoint //
    return sqrt(pow(this->get_radius(), 2) - pow(this->get_length() / 2, 2));
}

float Segment::get_eta()
{
    // Return eta angle (half the included angle) in radians //
    return this->get_angle() / 2;
}

float Segment::get_epsilon()
{
    // Returns signless epsilon angle in radians//
    if (this->bulge == 0)
    {
        return 0;
    }

    return abs(atan(this->bulge));
}

float Segment::get_phi()
{
    // Return signless phi angle in radians //

    if (this->bulge == 0)
    {
        return 0;
    }

    return abs((M_PIf - abs(this->get_angle()) / 2) / 2);
}

float Segment::get_gamma()
{
    // Returns signless gamma angle in radians //

    if (this->bulge == 0)
    {
        return 0;
    }

    return (M_PIf - abs(this->get_angle())) / 2;
}

bool Segment::is_same(Segment seg)
{
    // Returns true is the segment is the same //

    if (this->start.is_same(seg.start))
    {
        if (this->end.is_same(seg.end))
        {
            if (this->bulge == seg.bulge)
            {
                return true;
            }
        }
    }

    return false;
}

std::vector<Point> Segment::intersect(Segment seg, bool extend = false)
{
    // Determine intersections between self && seg//
    std::vector<Point> pts;
    if (this->bulge == 0 && seg.bulge == 0)
    {
        pts = this->intersect_line_line(seg, extend);
    }
    else if (this->bulge != 0 && seg.bulge != 0)
    {
        pts = this->intersect_circle_circle(seg, extend);
    }
    else if (this->bulge != 0 || seg.bulge != 0 && this->bulge == 0 || seg.bulge == 0)
    {
        pts = this->intersect_circle_line(seg, extend);
    }

    return pts;
}

std::vector<Point> Segment::intersect_line_line(Segment seg, bool extend = false)
{
    // Determine intersections between self && seg when both are line segments//

    Point a1 = this->start;
    Point a2 = this->end;
    Point b1 = seg.start;
    Point b2 = seg.end;
    std::vector<Point> pts;

    float ua_t = (b2.x - b1.x) * (a1.z - b1.z) - (b2.z - b1.z) * (a1.x - b1.x);
    float ub_t = (a2.x - a1.x) * (a1.z - b1.z) - (a2.z - a1.z) * (a1.x - b1.x);
    float u_b = (b2.z - b1.z) * (a2.x - a1.x) - (b2.x - b1.x) * (a2.z - a1.z);

    // if ((u_b != 0)){
    float ua = ua_t / u_b;
    float ub = ub_t / u_b;
    //}

    if (((0 <= ua && ua <= 1) && (0 <= ub && ub <= 1)) || extend)
    {
        // intersect true
        Point pt = Point(a1.x + ua * (a2.x - a1.x), a1.z + ua * (a2.z - a1.z));
        pts.push_back(pt);
    }

    return pts;
}

std::vector<Point> Segment::intersect_circle_line(Segment seg, bool extend = false)
{
    // Determine intersections between self && seg when one is a line segment && one is an arc segment//

    std::vector<Point> pts;
    // TODO: initialise segment using Segment() without the points and bulge
    Segment line = Segment(Point(), Point(), 0);
    Segment circle = Segment(Point(), Point(), 0);

    if (this->bulge == 0 && seg.bulge != 0)
    {
        line.start = this->start;
        line.end = this->end;
        circle.start = seg.start;
        circle.end = seg.end;
        circle.bulge = seg.bulge;
    }

    if (this->bulge != 0 && seg.bulge == 0)
    {
        line.start = seg.start;
        line.end = seg.end;
        circle.start = this->start;
        circle.end = this->end;
        circle.bulge = this->bulge;
    }

    Point c = circle.get_centre_point();
    float r = circle.get_radius();
    Point a1 = line.start;
    Point a2 = line.end;

    if (line.get_length() == 0)
    {
        return pts;
    }

    float a = (a2.x - a1.x) * (a2.x - a1.x) + (a2.z - a1.z) * (a2.z - a1.z);
    float b = 2 * ((a2.x - a1.x) * (a1.x - c.x) + (a2.z - a1.z) * (a1.z - c.z));
    float cc = pow(c.x, 2) + pow(c.z, 2) + pow(a1.x, 2) + pow(a1.z, 2) - 2 * (c.x * a1.x + c.z * a1.z) - pow(r, 2);

    float deter = pow(b, 2) - 4 * a * cc;
    if (deter < 0)
    {
        return pts;
    }

    float e = sqrt(deter);
    float u1 = (-b + e) / (2 * a);
    float u2 = (-b - e) / (2 * a);

    

    Point point = a1.lerp(a2, u1);
    if (circle.point_on_segment(point) && line.point_on_segment(point) || extend){
        pts.push_back(point);
    }

    point = a1.lerp(a2, u2);
    if (circle.point_on_segment(point) && line.point_on_segment(point) || extend){
        pts.push_back(point);
    }

    return pts;
}

std::vector<Point> Segment::intersect_circle_circle(Segment seg, bool extend = false)
{
    // Determine intersections between self and seg when both are arc segments//

    std::vector<Point> pts;
    Point c1 = this->get_centre_point();
    float r1 = this->get_radius();
    Point c2 = seg.get_centre_point();
    float r2 = seg.get_radius();

    //  Determine actual distance between circle centres
    float c_dist = c1.distance_to(c2);

    if (Utils::roundoff(c_dist, 5) >= Utils::roundoff(r1 + r2, 5))
    {
        //  too far apart to intersect or just touching
        return pts;
    }

    if (c_dist < abs(r1 - r2))
    {
        //  inside each other
        return pts;
    }

    if (c1.is_same(c2) || Utils::roundoff(c_dist, 5) == 0)
    {
        //  concentric
        return pts;
    }

    //  get the chord distance
    float a = (pow(r1, 2) - pow(r2, 2) + pow(c_dist, 2)) / (2 * c_dist);

    //  A**2 + B**2 = C**2 h**2 + a**2 = r1**2 therefore:
    float h = sqrt(pow(r1, 2) - pow(a, 2));
    Point p = c1.lerp(c2, a / c_dist);
    float b = h / c_dist;

    Point pt1 = Point(p.x - b * (c2.z - c1.z), p.z + b * (c2.x - c1.x));
    if (this->point_on_segment(pt1) && seg.point_on_segment(pt1))
    {
        pts.push_back(pt1);
    }

    Point pt2 = Point(p.x + b * (c2.z - c1.z), p.z - b * (c2.x - c1.x));
    if (this->point_on_segment(pt2) && seg.point_on_segment(pt2))
    {
        pts.push_back(pt2);
    }

    return pts;
}

bool Segment::point_on_segment(Point point)
{
    // Determine if point is on segment //
    if (this->bulge == 0)
    {

        float length = get_length();
        float sp = start.distance_to(point);
        float pe = point.distance_to(end);

        // if the distance start > point + point > end is equal to length, point is online
        if (Utils::roundoff(length, 5) == Utils::roundoff(sp + pe, 5))
        {
            return true;
        }

        return false;
    }
    else
    {
        //  Arc
        Point c = this->get_centre_point();
        float radius = this->get_radius();
        float sa = c.angle_to(this->start);
        float ea = c.angle_to(this->end);
        float pnt_ang = c.angle_to(point);

        //  if (the point isn't on the segment radius it's not a true intersection
        if (Utils::roundoff(c.distance_to(point), 2) != Utils::roundoff(radius, 2))
        {
            return false;
        }

        // if the point angle matches the start or end angles the point is on the arc
        if(sa == pnt_ang || pnt_ang == ea)
        {
            return true;
        }

        // check if the pnt_ang falls between the start and end angles
        return this->crossesAxis(sa, ea, pnt_ang);
    }
}

float Segment::distance_to_point(Point point){

    float APx = point.x - start.x;
    float APy = point.z - start.z;
    float ABx = end.x - start.x;
    float ABy = end.z  - start.z;

    float magAB2 = ABx * ABx + ABy * ABy;
    float ABdotAP = ABx * APx + ABy * APy;
    float t = ABdotAP / magAB2;

    // check if the point is < start or > end
    if (t > 0.0 && t < 1.0){
        float x = start.x + ABx * t;
        float z = start.z + ABy * t;
        Point p = Point(x, z);
        return p.distance_to(point); 
    }
    
    if (t < 0){
        return start.distance_to(point); 
    }

    return end.distance_to(point); 

    //TODO: Support arcs
}
