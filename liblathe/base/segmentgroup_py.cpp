#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "segmentgroup.h"
#include "stockstate.h"

namespace py = pybind11;

PYBIND11_MODULE(segmentgroup, m)
{
     // Register segment-group editing, offset and boundary-query operations with Python //
     using namespace liblathe;

     // optional module docstring
     m.doc() = "segmentgroup Class";

     py::class_<stock_preview::StockState>(m, "StockPreview")
         .def(py::init([](const std::vector<std::pair<double, double>>& vertices) {
              stock_preview::Polygon polygon;
              for (auto vertex : vertices) polygon.push_back({vertex.first, vertex.second});
              return stock_preview::StockState(std::move(polygon));
         }))
         .def("copy", [](const stock_preview::StockState& state) { return state; })
         .def("remove_feeds", [](stock_preview::StockState& state,
                                const std::vector<std::pair<double, double>>& vertices,
                                const std::vector<std::array<double, 4>>& moves) {
              stock_preview::Polygon tool;
              for (auto vertex : vertices) tool.push_back({vertex.first, vertex.second});
              tool = stock_preview::convex(std::move(tool));
              auto result = state;
              for (auto move : moves)
                   result.sweep(tool, {move[0], move[1]}, {move[2], move[3]});
              state = std::move(result);
         })
         .def("polygons", [](const stock_preview::StockState& state) {
              std::vector<std::vector<std::pair<double, double>>> result;
              for (const auto& polygon : state.polygons()) {
                   std::vector<std::pair<double, double>> vertices;
                   for (auto point : polygon) vertices.emplace_back(point.x, point.z);
                   result.push_back(std::move(vertices));
              }
              return result;
         })
         .def("edges", [](const stock_preview::StockState& state) {
              std::vector<std::array<double, 4>> result;
              for (auto edge : state.boundary())
                   result.push_back({edge.start.x, edge.start.z, edge.end.x, edge.end.z});
              return result;
         })
         .def_property_readonly("area", &stock_preview::StockState::materialArea)
         .def_property_readonly("uncertain_retentions", &stock_preview::StockState::retainedUncertain);

         py::class_<DefeatureResult>(m, "DefeatureResult")
             .def_readonly("contour", &DefeatureResult::contour,
                          "Collision-free simplified contour with certified connectors.")
             .def_readonly("samples", &DefeatureResult::samples,
                          "Accepted radial scan origins before connector construction and simplification.");

     // bindings to segmentgroup class
     py::class_<SegmentGroup>(m, "SegmentGroup")
         .def(py::init<>())
         .def_property_readonly_static("defeatureResolution", [](py::object) {
              return SegmentGroup::defeatureResolution;
         })
         .def_property_readonly_static("offsetTolerance", [](py::object) {
              return SegmentGroup::offsetTolerance;
         })
         .def("addSegment", &SegmentGroup::addSegment)
         .def("insertSegment", &SegmentGroup::insertSegment)
         .def("getSegments", &SegmentGroup::getSegments)
         .def("reversed", &SegmentGroup::reversed,
              "Return an independent group with reversed segment order, endpoints and arc bulges.")
         .def("reflectX", &SegmentGroup::reflectX, py::arg("radius") = 0,
              "Return an independent group mapped by X = radius - X, reversing arc bulges.")
         .def("extend", &SegmentGroup::extend)
         .def("count", &SegmentGroup::count)
         .def("boundbox", &SegmentGroup::boundbox)
         .def("getRadialContactPoint", &SegmentGroup::getRadialContactPoint,
              "Return the axial midpoint of the radially innermost edge, including arc extrema.")
         .def("intersectsGroup", &SegmentGroup::intersectsGroup)
         .def("offset", &SegmentGroup::offset,
              py::arg("step_over"), py::arg("extend_start") = false,
              "Extract an offset polyline with raw and simplified chord errors "
              "bounded by 0.05 model units in the closed signed-distance field. "
              "Optionally retain the contour beyond the profile's starting Z. "
              "Raises RuntimeError for detected zero-width branches, uncertifiable "
              "chords or fewer than two contour points. Does not guarantee completeness.")
         .def("defeature", &SegmentGroup::defeature)
         .def("defeatureWithSamples", &SegmentGroup::defeatureWithSamples,
              "Return the defeatured contour and accepted radial scan origins.")
         .def("validateToolSweep", &SegmentGroup::validateToolSweep,
              "Certify full-insert clearance throughout a straight translation. "
              "Raise RuntimeError for collisions or uncertifiable sweeps.")
         .def("validateToolSweeps", &SegmentGroup::validateToolSweeps,
              "Certify ordered (start, end) translations using one part/tool snapshot. "
              "Raise on the first collision or uncertifiable sweep; an empty list is a no-op.")
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
