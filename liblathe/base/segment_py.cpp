
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segment.h"

namespace py = pybind11;

PYBIND11_MODULE(segment, m) {

    // optional module docstring
    m.doc() = "segment Class";

    // bindings to segment class
    py::class_<Segment>(m, "Segment")
        .def(py::init<>())
        .def(py::init<Point&, Point&>())
        .def(py::init<Point&, Point&, float>())
        .def_readwrite("start", &Segment::start)
        .def_readwrite("end", &Segment::end)
        .def_readwrite("bulge", &Segment::bulge)
        .def("get_angle", &Segment::get_angle)
        .def("set_bulge", &Segment::set_bulge)
        .def("get_centre_point", &Segment::get_centre_point)
        .def("get_radius", &Segment::get_radius)
        .def("get_rotation", &Segment::get_rotation)
        .def("get_boundbox", &Segment::get_boundbox)
        .def("crossesAxis", &Segment::crossesAxis)
        .def("get_length", &Segment::get_length)
        .def("get_sagitta", &Segment::get_sagitta)
        .def("get_apothem", &Segment::get_apothem)
        .def("get_eta", &Segment::get_eta)
        .def("get_epsilon", &Segment::get_epsilon)
        .def("get_phi", &Segment::get_phi)
        .def("is_same", &Segment::is_same)
        .def("intersect", &Segment::intersect, "", py::arg(), py::arg("extend")=false)
        .def("point_on_segment", &Segment::point_on_segment)
        .def("distance_to_point", &Segment::distance_to_point);

}