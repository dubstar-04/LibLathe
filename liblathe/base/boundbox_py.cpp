
#include <pybind11/pybind11.h>

#include "boundbox.h"

namespace py = pybind11;

PYBIND11_MODULE(boundbox, m) {

    // optional module docstring
    m.doc() = "Boundbox Class";

    // bindings to BoundBox class
    py::class_<BoundBox>(m, "BoundBox")
        .def(py::init<Point&, Point&>())
        .def("x_length", &BoundBox::x_length)
        .def("z_length", &BoundBox::z_length)
        .def_readwrite("x_min", &BoundBox::x_min)
        .def_readwrite("z_min", &BoundBox::z_min)
        .def_readwrite("x_max", &BoundBox::x_max)
        .def_readwrite("z_max", &BoundBox::z_max);

}