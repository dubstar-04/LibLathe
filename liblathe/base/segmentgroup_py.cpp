#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segmentgroup.h"

namespace py = pybind11;

PYBIND11_MODULE(segmentgroup, m)
{

    // optional module docstring
    m.doc() = "segmentgroup Class";

    // bindings to segmentgroup class
    py::class_<SegmentGroup>(m, "SegmentGroup")
        .def(py::init<>())
        .def("addSegment", &SegmentGroup::addSegment)
        .def("insertSegment", &SegmentGroup::insertSegment)
        .def("getSegments", &SegmentGroup::getSegments)
        .def("extend", &SegmentGroup::extend)
        .def("count", &SegmentGroup::count)
        .def("boundbox", &SegmentGroup::boundbox)
        .def("intersectsGroup", &SegmentGroup::intersectsGroup)
        .def("offset", &SegmentGroup::offset)
        .def("defeature", &SegmentGroup::defeature)
        .def("validate", &SegmentGroup::validate)
        .def("fromPoints", &SegmentGroup::fromPoints)
        .def("reduce", &SegmentGroup::reduce)
        .def("sdv", &SegmentGroup::sdv)
        .def("isInside", &SegmentGroup::isInside);
}