#ifndef Segment_H
#define Segment_H

#define _USE_MATH_DEFINES
#include <math.h>

#include "boundbox.h"
#include "point.h"
#include "utils.h"



class Segment
{
    public:
        Segment(){};
        Segment(Point start, Point end);
        Segment(Point start, Point end, float bulge);
        ~Segment(){};

        Point start = Point();
        Point end = Point();
        float bulge = 0;

        float get_angle();
        void set_bulge(float angle);
        Point get_centre_point();
        float get_radius();
        float get_rotation();
        BoundBox get_boundbox();
        bool crossesAxis(float startAngle, float endAngle, float axisAngle);
        float get_length();
        float get_sagitta();
        float get_apothem();
        float get_eta();
        float get_epsilon();
        float get_phi();
        float get_gamma();
        bool is_same(Segment seg);
        std::vector<Point> intersect(Segment seg, bool extend);
        bool point_on_segment(Point point);
        float distance_to_point(Point point);
        

        private:
            std::vector<Point> intersect_line_line(Segment seg, bool extend);
            std::vector<Point> intersect_circle_line(Segment seg, bool extend);
            std::vector<Point> intersect_circle_circle(Segment seg, bool extend);


};

#endif





