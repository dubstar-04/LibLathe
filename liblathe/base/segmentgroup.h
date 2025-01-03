#ifndef SegmentGroup_H
#define SegmentGroup_H

#include <algorithm>

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
    bool intersectsGroup(SegmentGroup segment_group);
    SegmentGroup offset(float step_over);
    SegmentGroup defeature(BoundBox stock, SegmentGroup tool, bool allow_grooving);
    void validate();
    SegmentGroup fromPoints(std::vector<Point> points);
    std::vector<Point> reduce(std::vector<Point> &points, float tolerance);
    bool isInside(Point point);
    float sdv(Point point);

private:
    std::vector<Segment> segments;
    void rdp(std::vector<Point> &points, float tolerance, std::vector<Point> &out);
    SegmentGroup add(Point point);
    SegmentGroup copy();
};

#endif
