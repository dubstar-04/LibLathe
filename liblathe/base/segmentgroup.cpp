#include <iostream>
#include <cmath>
#include <stdexcept>
#include <array>
#include <limits>

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

bool SegmentGroup::intersectsGroup(SegmentGroup segmentGroup)
{
    // check if the segmentGroup intersects self //
    for (auto &segment : segmentGroup.getSegments())
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
    if (this->count() == 0)
    {
        throw std::invalid_argument("Cannot offset empty geometry");
    }
    if (!std::isfinite(step_over))
    {
        throw std::invalid_argument("Offset must be finite");
    }

    BoundBox bb = this->boundbox();
    // Pad the half-open root without extending the search past the axis.
    float padding = std::abs(step_over) + Quadtree::defaultPrecision;
    float xmin = std::min(0.0f, bb.XMin);
    float zmin = bb.ZMin - padding;
    float size = std::max(bb.XMax + padding - xmin, bb.ZLength() + 2 * padding);
    Point center = Point(xmin + size / 2, zmin + size / 2);

    Quadtree qt = Quadtree();
    qt.initialise(this, center, size, size);
    std::vector<Point> offset = qt.getOffset(step_over);
    offset.erase(std::unique(offset.begin(), offset.end(),
                             [](Point first, Point second) { return first.isSame(second); }),
                 offset.end());
    if (offset.empty())
    {
        throw std::runtime_error("Offset produced no points");
    }
    if (offset.size() < 2)
    {
        throw std::runtime_error("Offset produced fewer than two points");
    }

    // attempt simplification
    float resolution = 0.01;
    std::vector<Point> defeatured_points;
    this->rdp(offset, resolution, defeatured_points);
    this->validateOffsetContour(defeatured_points, step_over);
    return this->fromPoints(defeatured_points);
}

void SegmentGroup::validateOffsetContour(const std::vector<Point> &points, float offset)
{
    if (points.size() < 2)
        return;
    if (offset != 0)
    {
        std::vector<Segment> boundary = this->segments;
        const auto closure = this->axisClosure();
        boundary.insert(boundary.end(), closure.begin(), closure.end());
        for (const Point &point : points)
        {
            const double magnitude = std::max({1.0, std::abs(double(point.X)),
                                              std::abs(double(point.Z)), std::abs(double(offset))});
            const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() * magnitude;
            if (std::abs(offset) <= numerical)
                continue;
            std::vector<Point> nearest;
            for (auto &segment : boundary)
            {
                Point closest = segment.closestPoint(point);
                const double distance = std::hypot(double(closest.X) - point.X,
                                                   double(closest.Z) - point.Z);
                if (std::abs(distance - std::abs(offset)) > numerical)
                    continue;
                // Opposite nearest normals identify a zero-width level-set branch.
                for (const Point &other : nearest)
                {
                    if (std::hypot(double(closest.X) + other.X - 2 * double(point.X),
                                   double(closest.Z) + other.Z - 2 * double(point.Z)) <=
                        2 * numerical)
                        throw std::runtime_error(
                            "Offset contour contains a collapsed branch; "
                            "zero-width contours are not supported");
                }
                nearest.push_back(closest);
            }
        }
    }
    for (size_t i = 1; i < points.size(); ++i)
        this->validateOffsetChord(points[i - 1], points[i], offset);
}

void SegmentGroup::validateOffsetChord(Point start, Point end, float offset)
{
    Point midpoint = start.mid(end);
    const double residual = std::abs(double(this->sdv(midpoint)) - offset);
    const double magnitude = std::max({1.0, std::abs(double(midpoint.X)),
                                      std::abs(double(midpoint.Z)), std::abs(double(offset))});
    const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() * magnitude;
    if (residual > offsetTolerance)
        throw std::runtime_error(
            "Offset contour exceeds 0.05 model-unit accuracy; "
            "collapsed or disconnected contours are not supported");

    // The signed distance is 1-Lipschitz: bound the entire chord from its midpoint.
    const double radius = std::max(
        std::hypot(double(start.X) - midpoint.X, double(start.Z) - midpoint.Z),
        std::hypot(double(end.X) - midpoint.X, double(end.Z) - midpoint.Z));
    if (residual + numerical + radius <= offsetTolerance)
        return;
    if ((midpoint.X == start.X && midpoint.Z == start.Z) ||
        (midpoint.X == end.X && midpoint.Z == end.Z))
        throw std::runtime_error(
            "Cannot certify offset contour within 0.05 model units at coordinate precision");
    this->validateOffsetChord(start, midpoint, offset);
    this->validateOffsetChord(midpoint, end, offset);
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
    SegmentGroup segmentGroup = SegmentGroup();

    if (points.size() > 0)
    {
        for (int i = 0; i < points.size(); i++)
        {
            if (i >= 1)
            {
                Segment seg = Segment(points[i - 1], points[i]);
                segmentGroup.addSegment(seg);
            }
        }
    }

    return segmentGroup;
}

SegmentGroup SegmentGroup::copy()
{
    // create a copy of the segment group //
    SegmentGroup segmentGroup = SegmentGroup();

    for (auto &segment : this->segments)
    {
        Point start = Point(segment.start.X, segment.start.Z);
        Point end = Point(segment.end.X, segment.end.Z);
        segmentGroup.addSegment(Segment(start, end, segment.bulge));
    }

    return segmentGroup;
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

std::array<Segment, 3> SegmentGroup::axisClosure()
{
    if (this->segments.empty())
        throw std::invalid_argument("Cannot evaluate empty geometry");

    const Point start = this->segments.front().start;
    const Point end = this->segments.back().end;
    // Radial closures at the same Z overlap; retain only their uncancelled part.
    if (start.Z == end.Z)
        return {Segment(end, start), Segment(start, start), Segment(start, start)};
    return {
        Segment(Point(0, start.Z), start),
        Segment(end, Point(0, end.Z)),
        Segment(Point(0, end.Z), Point(0, start.Z))
    };
}

Point SegmentGroup::closestPoint(Point point, bool *onProfile)
{
    auto closure = this->axisClosure();
    if (!std::isfinite(point.X) || !std::isfinite(point.Z))
        throw std::invalid_argument("Query point must be finite");
    Point closest = this->segments.front().start;
    double closestDistance = std::numeric_limits<double>::infinity();
    bool closestOnProfile = true;
    auto consider = [&](Segment &segment, bool original) {
        Point pnt = segment.closestPoint(point);
        if (!std::isfinite(pnt.X) || !std::isfinite(pnt.Z))
            throw std::runtime_error("Boundary closest point is not finite");
        const double dx = double(pnt.X) - point.X;
        const double dz = double(pnt.Z) - point.Z;
        const double distance = dx * dx + dz * dz;
        if (distance < closestDistance)
        {
            closest = pnt;
            closestDistance = distance;
            closestOnProfile = original;
        }
    };
    for (auto &segment : this->segments)
        consider(segment, true);
    for (auto &segment : closure)
        consider(segment, false);
    if (onProfile != nullptr)
        *onProfile = closestOnProfile;
    return closest;
}

float SegmentGroup::sdv(Point point)
{
    const float distance = this->closestPoint(point).distanceTo(point);
    return this->isInside(point) ? -distance : distance;
}

bool SegmentGroup::isInside(Point point)
{
    auto closure = this->axisClosure();

    // Return -1 on the boundary; otherwise count crossings above the query.
    auto crossings = [&](Segment &segment) -> int {
        const Point start = segment.start;
        const Point end = segment.end;
        if (point.X == start.X && point.Z == start.Z)
            return -1;
        if (point.X == end.X && point.Z == end.Z)
            return -1;
        if (segment.bulge == 0 || (start.X == end.X && start.Z == end.Z))
        {
            const double dx = double(end.X) - start.X;
            const double dz = double(end.Z) - start.Z;
            const double cross = dx * (double(point.Z) - start.Z) -
                                 dz * (double(point.X) - start.X);
            if (cross == 0 &&
                point.X >= std::min(start.X, end.X) && point.X <= std::max(start.X, end.X) &&
                point.Z >= std::min(start.Z, end.Z) && point.Z <= std::max(start.Z, end.Z))
                return -1;
            if ((start.X > point.X) == (end.X > point.X))
                return 0;
            const double z = start.Z + (double(point.X) - start.X) * dz / dx;
            return z > point.Z ? 1 : 0;
        }

        const Point centre = segment.getCentrePoint();
        const double radius = segment.getRadius();
        const double pi = std::acos(-1.0);
        const double direction = segment.bulge > 0 ? -1 : 1;
        const double sweep = 4 * std::atan(std::abs(double(segment.bulge)));
        const double startAngle = std::atan2(double(start.Z) - centre.Z,
                                             double(start.X) - centre.X);
        auto progress = [&](double angle) {
            return std::fmod(direction * (angle - startAngle) + 2 * pi, 2 * pi);
        };
        const double px = double(point.X) - centre.X;
        const double pz = double(point.Z) - centre.Z;
        const double epsilon = 4 * std::numeric_limits<float>::epsilon();
        if (std::abs(px * px + pz * pz - radius * radius) <=
                epsilon * radius * radius &&
            progress(std::atan2(pz, px)) <= sweep + epsilon)
            return -1;

        // Split at X extrema so the same half-open endpoint rule works for arcs.
        std::array<std::pair<double, double>, 4> breaks;
        breaks[0] = {0, start.X};
        breaks[1] = {sweep, end.X};
        size_t count = 2;
        for (double angle : {0.0, pi})
        {
            const double position = progress(angle);
            if (position > 0 && position < sweep)
                breaks[count++] = {position, centre.X + (angle == 0 ? radius : -radius)};
        }
        std::sort(breaks.begin(), breaks.begin() + count);
        const double discriminant = radius * radius - px * px;
        if (discriminant <= 0)
            return 0;
        const double height = std::sqrt(discriminant);
        int result = 0;
        for (size_t i = 1; i < count; ++i)
        {
            if ((breaks[i - 1].second > point.X) == (breaks[i].second > point.X))
                continue;
            const double middle = startAngle + direction *
                                  (breaks[i - 1].first + breaks[i].first) / 2;
            const double z = centre.Z + (std::sin(middle) > 0 ? height : -height);
            if (z > point.Z)
                ++result;
        }
        return result;
    };

    int intersections = 0;
    for (auto &segment : this->segments)
    {
        const int count = crossings(segment);
        if (count < 0)
            return true;
        intersections += count;
    }
    for (auto &segment : closure)
    {
        const int count = crossings(segment);
        if (count < 0)
            return true;
        intersections += count;
    }
    return intersections % 2 != 0;
}
