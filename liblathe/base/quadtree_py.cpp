
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "quadtree.h"
#include "point.h"

namespace py = pybind11;

PYBIND11_MODULE(quadtree, m)
{

    // optional module docstring
    m.doc() = "Signed Distance Field";

    // bindings to Quadtree class
    py::class_<Quadtree>(m, "Quadtree")
        .def(py::init<>())
        .def("initialise", &Quadtree::initialise)
        .def("getOffset", &Quadtree::getOffset)
        .def("getNodes", &Quadtree::getNodes);

    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("center", &Node::center)
        .def_readwrite("width", &Node::width)
        .def_readwrite("height", &Node::height)
        .def_readwrite("sdv", &Node::sdv);
}