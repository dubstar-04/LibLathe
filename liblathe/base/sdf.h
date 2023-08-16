#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <vector>


int add(int i, int j) {
    return i + j;
}

#ifndef SDF_H
#define SDF_H

struct Point {
    Point(float &x, float &z) : x(x), z(z){ }
    float x;
    float z;
};

struct Segment {
    Point start;
    Point end;
};

class SDF
{
    public:
        SDF();
        ~SDF();

        void add_point(float, float);
        int point_count();
        Point closest(Point, Point, Point);
        std::vector<std::vector<float>> generate();

    private:
        std::vector<Point> points;
        bool isInside(Point);
        int intersect(Segment, Segment);
        float distance_to(Point, Point);
        
};

#endif

namespace py = pybind11;

PYBIND11_MODULE(sdf, m) {
    // optional module docstring
    m.doc() = "Signed Distance Field";

    // define add function
    m.def("add", &add, "A function which adds two numbers");

    // bindings to SDF class
    py::class_<SDF>(m, "SDF")
        .def(py::init<>())
        .def("add_point", &SDF::add_point)
        .def("point_count", &SDF::point_count)
        .def("closest", &SDF::closest)
        .def("generate", &SDF::generate);

    // binding to the point struct
    py::class_<Point>(m, "Point")
        .def(py::init<float&, float&>())
        .def_readwrite("x", &Point::x)
        .def_readwrite("z", &Point::z);
}