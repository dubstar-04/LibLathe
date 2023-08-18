
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "point.h"

namespace py = pybind11;

PYBIND11_MODULE(point, m) {

    // optional module docstring
    m.doc() = "Point Class";


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