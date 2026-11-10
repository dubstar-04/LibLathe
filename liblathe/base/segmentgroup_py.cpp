#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segmentgroup.h"

namespace py = pybind11;

PYBIND11_MODULE(segmentgroup, m)
{
     // Register segment-group editing, offset and boundary-query operations with Python //
     using namespace liblathe;

     // optional module docstring
     m.doc() = "segmentgroup Class";

     // bindings to segmentgroup class
     py::class_<SegmentGroup>(m, "SegmentGroup")
         .def(py::init<>())
         .def("addSegment", &SegmentGroup::addSegment)
         .def("insertSegment", &SegmentGroup::insertSegment)
         .def("getSegments", &SegmentGroup::getSegments)
         .def("reversed", &SegmentGroup::reversed,
              "Return an independent group with reversed segment order, endpoints and arc bulges.")
         .def("extend", &SegmentGroup::extend)
         .def("count", &SegmentGroup::count)
         .def("boundbox", &SegmentGroup::boundbox)
         .def("getRadialContactPoint", &SegmentGroup::getRadialContactPoint,
              "Return the axial midpoint of the radially innermost edge, including arc extrema.")
         .def("intersectsGroup", &SegmentGroup::intersectsGroup)
         .def("offset", &SegmentGroup::offset,
              "Extract an offset polyline with raw and simplified chord errors "
              "bounded by 0.05 model units in the closed signed-distance field. "
              "Raises RuntimeError for detected zero-width branches, uncertifiable "
              "chords or fewer than two contour points. Does not guarantee completeness.")
         .def("defeature", &SegmentGroup::defeature)
         .def("validateToolSweep", &SegmentGroup::validateToolSweep,
              "Certify full-insert clearance throughout a straight translation. "
              "Raise RuntimeError for collisions or uncertifiable sweeps.")
         .def("validate", &SegmentGroup::validate)
         .def("fromPoints", &SegmentGroup::fromPoints)
         .def("reduce", &SegmentGroup::reduce)
         .def("sdv", &SegmentGroup::sdv,
              "Signed distance to the profile and its axis closure: negative inside, "
              "zero on the boundary, positive outside. Empty geometry and nonfinite "
              "query points raise ValueError.")
         .def("isInside", &SegmentGroup::isInside,
              "Classify a point against the profile closed along the axis. "
              "Closed profiles add no edges; endpoints at the same Z close directly. "
              "Boundary points count as inside; empty geometry raises ValueError.");
}
