
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "point.h"

namespace py = pybind11;

PYBIND11_MODULE(point, m)
{

    // optional module docstring
    m.doc() = "Point Class";

    // bindings to Point class
    py::class_<Point>(m, "Point")
        .def(py::init<float &, float &>())
        .def(py::init<>())
        .def_readwrite("X", &Point::X)
        .def_readwrite("Z", &Point::Z)
        .def("distanceTo", &Point::distanceTo)
        .def("angleTo", &Point::angleTo)
        .def("nearest", &Point::nearest)
        .def("isSame", &Point::isSame)
        .def("sub", &Point::sub)
        .def("add", &Point::add)
        .def("multiply", &Point::multiply)
        .def("lerp", &Point::lerp)
        .def("normaliseTo", &Point::normaliseTo)
        .def("rotate", &Point::rotate)
        .def("mid", &Point::mid)
        .def("project", &Point::project);
}