
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segment.h"

namespace py = pybind11;

PYBIND11_MODULE(segment, m)
{

    // optional module docstring
    m.doc() = "segment Class";

    // bindings to segment class
    py::class_<Segment>(m, "Segment")
        .def(py::init<>())
        .def(py::init<Point &, Point &>())
        .def(py::init<Point &, Point &, float>())
        .def_readwrite("start", &Segment::start)
        .def_readwrite("end", &Segment::end)
        .def_readwrite("bulge", &Segment::bulge)
        .def("getAngle", &Segment::getAngle)
        .def("setBulge", &Segment::setBulge)
        .def("getCentrePoint", &Segment::getCentrePoint)
        .def("getRadius", &Segment::getRadius)
        .def("getRotation", &Segment::getRotation)
        .def("Boundbox", &Segment::Boundbox)
        .def("crossesAxis", &Segment::crossesAxis)
        .def("getLength", &Segment::getLength)
        .def("getSagitta", &Segment::getSagitta)
        .def("getApothem", &Segment::getApothem)
        .def("getEta", &Segment::getEta)
        .def("getEpsilon", &Segment::getEpsilon)
        .def("getPhi", &Segment::getPhi)
        .def("isSame", &Segment::isSame)
        .def("intersect", &Segment::intersect, "", py::arg(), py::arg("extend") = false)
        .def("pointOnSegment", &Segment::pointOnSegment)
        .def("distanceToPoint", &Segment::distanceToPoint);
}