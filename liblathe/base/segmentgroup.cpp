#include <iostream>

#include "segmentgroup.h"

SegmentGroup::SegmentGroup()
{
}

void SegmentGroup::addSegment(Segment segment)
{
    // Add segment to group //
    this->segments.push_back(segment);
}

void SegmentGroup::insertSegment(Segment segment, int position)
{
    // Insert segment into group at position //
    segments.insert(segments.begin() + position, segment);
}

std::vector<Segment> SegmentGroup::getSegments()
{
    // Return segments //
    return this->segments;
}

void SegmentGroup::extend(SegmentGroup segmentgroup)
{
    // Add segment group to this segmentgroup //
    std::vector<Segment> segs = segmentgroup.getSegments();
    this->segments.insert(segments.end(), segs.begin(), segs.end());
}

int SegmentGroup::count()
{
    // Return the number of segments in the segmentgroup //
    return this->segments.size();
}

BoundBox SegmentGroup::boundbox()
{
    // Return the boundbox for the segmentgroup //

    if (this->count() == 0)
    {
        return BoundBox(Point(), Point());
    }

    std::vector<float> xvalues;
    std::vector<float> zvalues;

    // collect all points from each segment by direction
    for (auto &segment : this->segments)
    {
        BoundBox bb = segment.Boundbox();

        xvalues.push_back(bb.XMin);
        xvalues.push_back(bb.XMax);

        zvalues.push_back(bb.ZMin);
        zvalues.push_back(bb.ZMax);
    }

    float XMin = *std::min_element(std::begin(xvalues), std::end(xvalues));
    float XMax = *std::max_element(std::begin(xvalues), std::end(xvalues));
    float ZMin = *std::min_element(zvalues.begin(), zvalues.end());
    float ZMax = *std::max_element(zvalues.begin(), zvalues.end());

    Point pt1 = Point(XMin, ZMin);
    Point pt2 = Point(XMax, ZMax);
    BoundBox segmentgroupBoundBox = BoundBox(pt1, pt2);

    return segmentgroupBoundBox;
}

bool SegmentGroup::intersectsGroup(SegmentGroup segment_group)
{
    // check if the segment_group intersects self //
    for (auto &segment : segment_group.getSegments())
    {
        for (auto &seg : this->segments)
        {
            // TODO: remove false from intersect call
            std::vector<Point> points = segment.intersect(seg, false);
            if (points.size() > 0)
            {
                return true;
            }
        }
    }

    return false;
}

SegmentGroup SegmentGroup::offset(float step_over)
{
    // Create an offset segmentgroup by the distance of step_over //

    // TODO: investigate:
    // 1. using a square node - will this affect precision / performance
    // 2. optimise the size only needs to be slightly bigger than the part + the offset
    // 3. remove unused nodes
    // 4. store the points as nodes are being evaluated rather than searching the nodes later
    // 5. effects of scaling the segment group and quadtree

    BoundBox bb = this->boundbox();
    float height = bb.XLength() + 10;
    float width = bb.ZLength(); //+ 10;

    Point center = Point(height / 2, bb.ZMin + width / 2);

    Quadtree qt = Quadtree();
    qt.initialise(this, center, width, height);
    std::vector<Point> offset = qt.getOffset(step_over);

    // attempt simplification
    float resolution = 0.01;
    std::vector<Point> defeatured_points;
    this->rdp(offset, resolution, defeatured_points);
    return this->fromPoints(defeatured_points);
}

SegmentGroup SegmentGroup::defeature(BoundBox stock, SegmentGroup tool, bool allow_grooving = false)
{
    // Defeature the segment group. Remove features that cannot be turned. e.g. undercuts / grooves etc //

    float XMin = 0;
    float XMax = stock.XMax;
    float ZMin = stock.ZMin;
    float ZMax = stock.ZMax;
    float resolution = 0.01;

    std::vector<Point> points;

    // get start position
    Point start = Point(0, this->boundbox().ZMax); // segments[0].start;
    SegmentGroup tool_shape = tool.add(start);

    if (start.X > 0)
    {
        throw std::runtime_error("segment groups first segment must be at x = 0");
    }

    if (this->boundbox().ZMax < stock.ZMax)
    {
        while (intersectsGroup(tool_shape))
        {
            // move the tool along the z axis until it no longer intersects the part.
            start = start.add(Point(0, resolution));
            tool_shape = tool.add(start);
        }

        points.push_back(start);
    }

    float z_pos = start.Z;
    while (z_pos > ZMin)
    {
        // test for intersection at z with a single segment
        Segment test_segment = Segment(Point(XMax, z_pos), Point(XMin, z_pos));
        for (auto seg : this->segments)
        {
            // TODO: remove the bool false from the segment call
            std::vector<Point> pts = test_segment.intersect(seg, false);
            if (pts.size() > 0)
            {
                float x_pos = pts[0].X - resolution;
                while (x_pos < (pts[0].X + resolution))
                {
                    Point iteration_position = Point(x_pos, z_pos);
                    SegmentGroup tool_shape = tool.add(iteration_position);
                    if (!intersectsGroup(tool_shape))
                    {

                        // if allow_grooving is false
                        if (points.size() > 1 && allow_grooving == false)
                        {
                            float last_x = points.back().X;
                            if (x_pos < last_x)
                            {
                                iteration_position.X = last_x;
                            }
                        }

                        points.push_back(iteration_position);
                        break;
                    }
                    x_pos += resolution * 0.5;
                }
                break;
            }
        }

        z_pos -= resolution;
    }

    // attempt simplification
    std::vector<Point> defeatured_points;
    this->rdp(points, resolution, defeatured_points);
    return this->fromPoints(defeatured_points);
}

SegmentGroup SegmentGroup::add(Point point)
{
    // add point to each segment of the segment group //
    // TODO: this could be done in segment using the add method of the point class
    SegmentGroup out;

    for (auto seg : this->segments)
    {
        Point start = Point(seg.start.X + point.X, seg.start.Z + point.Z);
        Point end = Point(seg.end.X + point.X, seg.end.Z + point.Z);
        Segment new_seg = Segment(start, end);
        out.addSegment(new_seg);
    }

    return out;
}

SegmentGroup SegmentGroup::fromPoints(std::vector<Point> points)
{
    // create a segment group from a vector of points //
    SegmentGroup segment_group = SegmentGroup();

    if (points.size() > 0)
    {
        for (int i = 0; i < points.size(); i++)
        {
            if (i >= 1)
            {
                Segment seg = Segment(points[i - 1], points[i]);
                segment_group.addSegment(seg);
            }
        }
    }

    return segment_group;
}

SegmentGroup SegmentGroup::copy()
{
    // create a copy of the segment group //
    SegmentGroup segment_group = SegmentGroup();

    for (auto &segment : this->segments)
    {
        Point start = Point(segment.start.X, segment.start.Z);
        Point end = Point(segment.end.X, segment.end.Z);
        segment_group.addSegment(Segment(start, end, segment.bulge));
    }

    return segment_group;
}

std::vector<Point> SegmentGroup::reduce(std::vector<Point> &points, float tolerance)
{
    std::vector<Point> out;
    this->rdp(points, tolerance, out);
    return out;
}

void SegmentGroup::rdp(std::vector<Point> &points, float tolerance, std::vector<Point> &out)
{
    // reduce the number of points in the segmentgroup using a Ramer–Douglas–Peucker algorithm

    if (points.size() < 2)
    {
        throw std::runtime_error("SegmentGroup error not enough points to simplify group");
    }

    // Find the point with the maximum distance from line between start and end
    double dmax = 0.0;
    size_t index = 0;
    size_t end = points.size() - 1;
    for (size_t i = 1; i < end; i++)
    {
        double d = Segment(points[0], points[end]).distanceToPoint(points[i]);
        if (d > dmax)
        {
            index = i;
            dmax = d;
        }
    }

    // If max distance is greater than tolerance, recursively simplify
    if (dmax > tolerance)
    {
        // Recursive call
        std::vector<Point> recResults1;
        std::vector<Point> recResults2;
        std::vector<Point> firstLine(points.begin(), points.begin() + index + 1);
        std::vector<Point> lastLine(points.begin() + index, points.end());
        this->rdp(firstLine, tolerance, recResults1);
        this->rdp(lastLine, tolerance, recResults2);

        // Build the result list
        out.assign(recResults1.begin(), recResults1.end() - 1);
        out.insert(out.end(), recResults2.begin(), recResults2.end());
        if (out.size() < 2)
        {
            throw std::runtime_error("SegmentGroup error when performing point reduction");
        }
    }
    else
    {
        // Just return start and end points
        out.clear();
        out.push_back(points[0]);
        out.push_back(points[end]);
    }
}

void SegmentGroup::validate()
{
    // validate the segment group//

    // check each segment is connected

    // check that the group is open i.e, the start and end points are not connected

    // check that the start and end points are at x = 0 (only valid for the primary group / part shape)
}

float SegmentGroup::sdv(Point point)
{
    // return a signed distance value to the closest point on the segments //
    float sdv;

    bool inside = this->isInside(point);
    float dist_clst_pnt = std::numeric_limits<float>::infinity();

    // find closest point on the segments
    for (auto &segment : this->segments)
    {
        float clst_dist = segment.distanceToPoint(point);
        dist_clst_pnt = std::min(clst_dist, dist_clst_pnt);
    }

    sdv = abs(dist_clst_pnt);
    if (inside)
    {
        sdv = -sdv;
    }

    return sdv;
}

bool SegmentGroup::isInside(Point point)
{
    // determine if point is inside the segmentgroup //
    int intersections = 0;

    // generate a ray to perform the crossing
    float x = point.X;
    // ensure that the ray starts outside the segments boundbox
    float z = this->boundbox().ZMax + 10;
    Segment ray = Segment(Point(x, z), point);

    // TODO: consider is there is a better way to ensure the start and end are at X0
    //  get a copy of the segment group
    SegmentGroup segmentGroupCopy = this->copy();

    // check the group starts at X0
    if (segmentGroupCopy.getSegments().front().start.X != 0)
    {
        // add a new segment to fill between the group start and x = 0 //
        Point end_point = segmentGroupCopy.getSegments().front().start;
        Point start_point = Point(0, end_point.Z);
        Segment start_filler_segment = Segment(start_point, end_point);
        segmentGroupCopy.insertSegment(start_filler_segment, 0);
    }

    // check the group end at X0
    if (segmentGroupCopy.getSegments().back().end.X != 0)
    {
        // add a new segment to fill between the group end and x = 0 //
        Point start_point = segmentGroupCopy.getSegments().back().end;
        Point end_point = Point(0, start_point.Z);
        Segment end_filler_segment = Segment(start_point, end_point);
        segmentGroupCopy.addSegment(end_filler_segment);
    }

    // collect the number of times ray intersects the segments
    for (auto &segment : segmentGroupCopy.segments)
    {
        std::vector<Point> pnts = ray.intersect(segment, false);
        intersections += pnts.size();
    }

    if (intersections % 2 == 0 && intersections > 0 || intersections == 0)
    {
        // even
        return false;
    }
    // odd
    return true;
}
