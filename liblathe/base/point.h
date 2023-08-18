
#define _USE_MATH_DEFINES

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#ifndef Point_H
#define Point_H

class Point
{
    public:
        Point(float x, float z);
        ~Point();
        
        float x;
        float z;
        float distance_to(Point pt);
        float angle_to(Point pt);
        Point nearest(std::vector<Point> pts);
        bool is_same(Point pt);
        Point sub(Point pt);
        Point add(Point pt);
        Point multiply(float val);
        Point lerp(Point pt, float t);
        Point normalise_to(Point pt);
        Point rotate(Point center, float angle);
        Point mid(Point pt);
        Point project(float angle, float distance);

};

namespace py = pybind11;

PYBIND11_MODULE(point, m) {
    // optional module docstring
    m.doc() = "2D Point Class";

    // bindings to Point class
    py::class_<Point>(m, "Point")
        .def(py::init<float&, float&>())
        .def(py::init<>())
        .def_readwrite("x", &Point::x)
        .def_readwrite("z", &Point::z)
        .def("distance_to", &Point::distance_to)
        .def("angle_to", &Point::angle_to)
        .def("nearest", &Point::nearest)
        .def("is_same", &Point::is_same)        
        .def("sub", &Point::sub)
        .def("add", &Point::add)
        .def("multiply", &Point::multiply)
        .def("lerp", &Point::lerp)
        .def("normalise_to", &Point::normalise_to)
        .def("rotate", &Point::rotate)
        .def("mid", &Point::mid)
        .def("project", &Point::project);

}

#endif