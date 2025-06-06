
#include <pybind11/pybind11.h>

#include "boundbox.h"

namespace py = pybind11;

PYBIND11_MODULE(boundbox, m)
{

    // optional module docstring
    m.doc() = "Boundbox Class";

    // bindings to BoundBox class
    py::class_<BoundBox>(m, "BoundBox")
        .def(py::init<Point &, Point &>())
        .def("XLength", &BoundBox::XLength)
        .def("ZLength", &BoundBox::ZLength)
        .def_readwrite("XMin", &BoundBox::XMin)
        .def_readwrite("ZMin", &BoundBox::ZMin)
        .def_readwrite("XMax", &BoundBox::XMax)
        .def_readwrite("ZMax", &BoundBox::ZMax);
}