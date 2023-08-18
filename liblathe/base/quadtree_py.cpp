
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "quadtree.h"
#include "point.h"

namespace py = pybind11;

PYBIND11_MODULE(quadtree, m) {

    // optional module docstring
    m.doc() = "Signed Distance Field";

    // bindings to Quadtree class
    py::class_<Quadtree>(m, "Quadtree")
        .def(py::init<>())
        .def("add_point", &Quadtree::add_point)
        .def("point_count", &Quadtree::point_count)
        .def("add_base_node", &Quadtree::add_base_node)
        .def("get_offset", &Quadtree::get_offset)
        .def("get_nodes", &Quadtree::get_nodes);

    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("center", &Node::center)
        .def_readwrite("width", &Node::width)
        .def_readwrite("height", &Node::height)
        .def_readwrite("sdv", &Node::sdv);

}