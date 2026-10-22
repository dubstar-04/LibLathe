
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
        .def("initialise", &Quadtree::initialise, py::keep_alive<1, 2>(),
             "Retain source geometry until this tree is destroyed, including "
             "geometry supplied by earlier initialise calls. Invalid geometry "
             "pointers or root bounds raise ValueError without changing configuration.")
        .def("getOffset", &Quadtree::getOffset,
             "Return offset points, or an empty list when no contour is found. "
             "Use the axis-closed distance field but exclude artificial-closure "
             "candidates, retaining original geometry on exact ties and the start-Z clip. "
             "Zero offsets sample both sides; projected candidates are checked "
             "against the requested signed distance. "
             "Raise RuntimeError before initialisation, or ValueError for empty "
             "geometry or nonfinite offsets.")
        .def("getNodes", &Quadtree::getNodes);

    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("center", &Node::center)
        .def_readwrite("width", &Node::width)
        .def_readwrite("height", &Node::height)
        .def_readwrite("sdv", &Node::sdv);
}