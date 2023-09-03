#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segmentgroup.h"

namespace py = pybind11;

PYBIND11_MODULE(segmentgroup, m) {

    // optional module docstring
    m.doc() = "segmentgroup Class";

    // bindings to segmentgroup class
    py::class_<SegmentGroup>(m, "SegmentGroup")
        .def(py::init<>())
        .def("add_segment", &SegmentGroup::add_segment)
        .def("insert_segment", &SegmentGroup::insert_segment)
        .def("get_segments", &SegmentGroup::get_segments)
        .def("extend", &SegmentGroup::extend)
        .def("count", &SegmentGroup::count)
        .def("boundbox", &SegmentGroup::boundbox)
        .def("intersects_group", &SegmentGroup::intersects_group)
        .def("offset", &SegmentGroup::offset)
        .def("defeature", &SegmentGroup::defeature)
        .def("validate", &SegmentGroup::validate)
        .def("from_points", &SegmentGroup::from_points)
        .def("get_rdp", &SegmentGroup::get_rdp)
        .def("sdv", &SegmentGroup::sdv)
        .def("isInside", &SegmentGroup::isInside);
}