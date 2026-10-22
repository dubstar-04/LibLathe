#ifndef SegmentGroup_H
#define SegmentGroup_H

#include <algorithm>
#include <array>

#include "boundbox.h"
#include "point.h"
#include "utils.h"
#include "segment.h"
#include "quadtree.h"

class SegmentGroup
{
public:
    SegmentGroup();
    ~SegmentGroup() {};

    void addSegment(Segment segment);
    void insertSegment(Segment segment, int position);
    std::vector<Segment> getSegments();
    void extend(SegmentGroup segmentgroup);
    int count();
    BoundBox boundbox();
    bool intersectsGroup(SegmentGroup segmentGroup);
    // Throws invalid_argument for empty geometry or nonfinite offsets,
    // runtime_error if fewer than two distinct contour points are produced.
    SegmentGroup offset(float step_over);
    SegmentGroup defeature(BoundBox stock, SegmentGroup tool, bool allow_grooving);
    void validate();
    SegmentGroup fromPoints(std::vector<Point> points);
    std::vector<Point> reduce(std::vector<Point> &points, float tolerance);
    // Ordered, connected lines/arcs must form a simple region with their axis
    // closure. Open endpoints close radially to X=0 and along the axis.
    // Endpoints at the same Z close directly; closed profiles add no edges.
    // Boundary points count as inside. Empty geometry throws invalid_argument.
    bool isInside(Point point);
    // Signed distance to that complete boundary: negative inside, zero on it,
    // positive outside. Query points must be finite.
    float sdv(Point point);
    // Nearest point on the same boundary. Original geometry wins exact ties.
    // If supplied, onProfile distinguishes original from artificial edges.
    Point closestPoint(Point point, bool *onProfile = nullptr);

private:
    std::vector<Segment> segments;
    std::array<Segment, 3> axisClosure();
    void rdp(std::vector<Point> &points, float tolerance, std::vector<Point> &out);
    SegmentGroup add(Point point);
    SegmentGroup copy();
};

#endif
