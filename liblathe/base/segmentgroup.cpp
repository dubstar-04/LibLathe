#include <iostream>
#include <cmath>
#include <stdexcept>
#include <array>
#include <limits>
#include <string>

#include "segmentgroup.h"
#include "quadtree.h"

namespace liblathe
{

    namespace
    {
        BoundBox intersectionBounds(Segment segment)
        {
            // Pad segment bounds conservatively for the intersection routines' rounding tolerances //
            BoundBox bounds = segment.Boundbox();
            const float scale = std::max({1.0f, std::abs(bounds.XMin), std::abs(bounds.XMax),
                                          std::abs(bounds.ZMin), std::abs(bounds.ZMax)});
            // The arc narrow phase rounds radial membership to two decimals.
            const float padding = 1e-4f + (segment.bulge != 0 ? 0.01f : 0.0f) +
                                  4 * std::numeric_limits<float>::epsilon() * scale;
            bounds.XMin -= padding;
            bounds.XMax += padding;
            bounds.ZMin -= padding;
            bounds.ZMax += padding;
            return bounds;
        }

        struct IntersectionSegment
        {
            Segment segment;
            BoundBox bounds;
            explicit IntersectionSegment(Segment source)
                : segment(source), bounds(intersectionBounds(source))
            {
                // Cache a segment and its padded bounds for repeated intersection tests //
            }
        };

        std::vector<IntersectionSegment> prepareIntersections(const std::vector<Segment> &segments)
        {
            // Prepare segment bounds for broad-phase intersection pruning //
            std::vector<IntersectionSegment> prepared;
            prepared.reserve(segments.size());
            for (const auto &segment : segments)
                prepared.emplace_back(segment);
            return prepared;
        }

        bool boundsOverlap(const BoundBox &first, const BoundBox &second)
        {
            // Test whether two axis-aligned bounds overlap or touch //
            return !(first.XMax < second.XMin || first.XMin > second.XMax ||
                     first.ZMax < second.ZMin || first.ZMin > second.ZMax);
        }

        bool intersectsAt(const std::vector<IntersectionSegment> &part,
                          const std::vector<IntersectionSegment> &tool, const Point &position)
        {
            // Test translated tool edges against part edges, pruning disjoint bounds //
            for (const auto &edge : tool)
            {
                BoundBox bounds = edge.bounds;
                bounds.XMin += position.X;
                bounds.XMax += position.X;
                bounds.ZMin += position.Z;
                bounds.ZMax += position.Z;
                for (const auto &target : part)
                {
                    if (!boundsOverlap(bounds, target.bounds))
                        continue;
                    Segment translated(
                        Point(edge.segment.start.X + position.X, edge.segment.start.Z + position.Z),
                        Point(edge.segment.end.X + position.X, edge.segment.end.Z + position.Z),
                        edge.segment.bulge);
                    if (!translated.intersect(target.segment, false).empty())
                        return true;
                }
            }
            return false;
        }
    }

    SegmentGroup::SegmentGroup()
    {
        // Create an empty ordered segment group //
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
        // Return a copy of the group's ordered segments //
        return this->segments;
    }

    const Point &SegmentGroup::getStartPoint() const
    {
        // Return the first segment's start point without copying, rejecting empty geometry //
        if (this->segments.empty())
            throw std::invalid_argument("Cannot get start point of empty geometry");
        return this->segments.front().start;
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
        // Test boundary intersections between groups without checking region containment //
        return intersectsAt(prepareIntersections(this->segments),
                            prepareIntersections(segmentGroup.segments), Point());
    }

    SegmentGroup SegmentGroup::offset(float step_over, bool extend_start)
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
        if (step_over == 0 && std::all_of(this->segments.begin(), this->segments.end(),
                                          [](const Segment &edge)
                                          { return edge.bulge == 0; }))
            return this->copy();

        BoundBox bb = this->boundbox();
        // Pad the half-open root without extending the search past the axis.
        float padding = std::abs(step_over) + Quadtree::defaultPrecision;
        float xmin = std::min(0.0f, bb.XMin);
        float zmin = bb.ZMin - padding;
        float size = std::max(bb.XMax + padding - xmin, bb.ZLength() + 2 * padding);
        Point center = Point(xmin + size / 2, zmin + size / 2);

        Quadtree qt = Quadtree();
        qt.initialise(this, center, size, size);
        std::vector<Point> offset = qt.getOffset(step_over, extend_start);
        offset.erase(std::unique(offset.begin(), offset.end(),
                                 [](Point first, Point second)
                                 { return first.isSame(second); }),
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
        qt.validateContour(defeatured_points);
        return this->fromPoints(defeatured_points);
    }

    void SegmentGroup::validateOffsetContour(const std::vector<Point> &points, float offset)
    {
        // Validate an offset polyline against a freshly prepared axis-closed boundary //
        this->prepareGeometry().validateContour(points, offset);
    }

    void SegmentGroup::validateToolSweep(SegmentGroup tool, Point start, Point end)
    {
        // Certify a full insert translation against the prepared axis-closed part region //
        const auto partGeometry = this->prepareGeometry();
        const auto toolGeometry = tool.prepareGeometry();
        partGeometry.validateToolSweep(toolGeometry, start, end);
    }

    void SegmentGroup::validateToolSweeps(
        const SegmentGroup &tool, const std::vector<std::pair<Point, Point>> &moves)
    {
        if (moves.empty())
            return;
        const auto partGeometry = this->prepareGeometry();
        auto toolSnapshot = tool;
        const auto toolGeometry = toolSnapshot.prepareGeometry();
        for (size_t index = 0; index < moves.size(); ++index)
        {
            const auto &move = moves[index];
            try
            {
                partGeometry.validateToolSweep(toolGeometry, move.first, move.second);
            }
            catch (const std::runtime_error &error)
            {
                throw std::runtime_error("Tool sweep " + std::to_string(index) + " (" +
                                         std::to_string(move.first.X) + ", " + std::to_string(move.first.Z) +
                                         ") -> (" + std::to_string(move.second.X) + ", " +
                                         std::to_string(move.second.Z) + "): " + error.what());
            }
        }
    }

    void SegmentGroup::PreparedGeometry::validateToolSweep(
        const PreparedGeometry &tool, Point start, Point end) const
    {
        auto bounds = tool.boundaryBounds.front();
        for (size_t index = 1; index < tool.originalCount; ++index)
        {
            const auto &edge = tool.boundaryBounds[index];
            bounds.XMin = std::min(bounds.XMin, edge.XMin);
            bounds.XMax = std::max(bounds.XMax, edge.XMax);
            bounds.ZMin = std::min(bounds.ZMin, edge.ZMin);
            bounds.ZMax = std::max(bounds.ZMax, edge.ZMax);
        }
        const double span = std::min(bounds.XLength(), bounds.ZLength());
        const double dx = double(end.X) - start.X;
        const double dz = double(end.Z) - start.Z;
        const double travel = std::hypot(dx, dz);
        if (!std::isfinite(travel) || !std::isfinite(span) || span <= 0)
            throw std::invalid_argument("Tool sweep requires finite coordinates and positive insert X/Z extents");
        const double count = std::max(1.0, std::ceil(travel / span));
        if (count >= double(std::numeric_limits<size_t>::max()))
            throw std::runtime_error("Tool sweep requires too many translation spans");
        // Bound each translation's subdivision work without changing the swept path or clearance tests.
        Point previous = start;
        for (size_t index = 1; index <= static_cast<size_t>(count); ++index)
        {
            const double fraction = index / count;
            const Point next = index == static_cast<size_t>(count)
                                   ? end
                                   : Point(start.X + fraction * dx, start.Z + fraction * dz);
            this->validateToolSweepSpan(tool, previous, next);
            previous = next;
        }
    }

    void SegmentGroup::PreparedGeometry::validateContour(
        const std::vector<Point> &points, float offset) const
    {
        // Reject collapsed offset branches and certify each polyline chord against the distance field //
        if (points.size() < 2)
            return;
        if (offset != 0)
        {
            for (const Point &point : points)
            {
                const double magnitude = std::max({1.0, std::abs(double(point.X)),
                                                   std::abs(double(point.Z)), std::abs(double(offset))});
                const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() * magnitude;
                if (std::abs(offset) <= numerical)
                    continue;
                std::vector<Point> nearest;
                for (const auto &prepared : this->boundary)
                {
                    Point closest = prepared.segment.closestPointPrepared(point, prepared.arc);
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
            this->validateChord(points[i - 1], points[i], offset);
    }

    void SegmentGroup::PreparedGeometry::validateChord(Point start, Point end, float offset) const
    {
        // Recursively certify a chord's offset error, throwing when accuracy cannot be established //
        Point midpoint = start.mid(end);
        const double residual = std::abs(double(this->sdv(midpoint)) - offset);
        const double magnitude = std::max({1.0, std::abs(double(midpoint.X)),
                                           std::abs(double(midpoint.Z)), std::abs(double(offset))});
        const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() * magnitude;
        if (residual > offsetTolerance)
            throw std::runtime_error(
                "Offset contour exceeds 0.05 model-unit accuracy; "
                "collapsed or disconnected contours are not supported; chord (" +
                std::to_string(start.X) + ", " + std::to_string(start.Z) + ") to (" +
                std::to_string(end.X) + ", " + std::to_string(end.Z) +
                "), midpoint error " + std::to_string(residual));

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
        this->validateChord(start, midpoint, offset);
        this->validateChord(midpoint, end, offset);
    }

    Point SegmentGroup::getRadialContactPoint()
    {
        // Locate the axial midpoint of the insert's radially innermost edge, including arc extrema //
        const auto toolBounds = this->boundbox();
        std::vector<Point> contactCandidates;
        for (auto edge : this->segments)
        {
            contactCandidates.push_back(edge.start);
            contactCandidates.push_back(edge.end);
            if (edge.bulge != 0)
                contactCandidates.push_back(edge.closestPoint(Point(toolBounds.XMin, edge.getCentrePoint().Z)));
        }
        float contactZMin = std::numeric_limits<float>::infinity();
        float contactZMax = -std::numeric_limits<float>::infinity();
        const float contactTolerance = 4 * std::numeric_limits<float>::epsilon() *
                                       std::max(1.0f, std::abs(toolBounds.XMin));
        for (const Point &candidate : contactCandidates)
        {
            if (std::abs(candidate.X - toolBounds.XMin) <= contactTolerance)
            {
                contactZMin = std::min(contactZMin, candidate.Z);
                contactZMax = std::max(contactZMax, candidate.Z);
            }
        }
        if (!std::isfinite(contactZMin) || !std::isfinite(contactZMax))
            throw std::runtime_error("Cannot locate the radially innermost insert edge");
        return Point(toolBounds.XMin, (contactZMin + contactZMax) * 0.5f);
    }

    SegmentGroup SegmentGroup::defeature(BoundBox stock, SegmentGroup tool, bool allow_grooving = false)
    {
        // Build a tool-origin boundary with full-insert clearance and certified connectors //

        float ZMin = stock.ZMin;
        const float resolution = defeatureResolution;

        std::vector<Point> points;

        // get start position
        BoundBox partBounds = this->boundbox();
        const auto partGeometry = this->prepareGeometry();
        const auto toolGeometry = tool.prepareGeometry();
        const auto toolBounds = tool.boundbox();
        double collisionRadius = 0;
        const auto interiorRadius = [&](const PreparedGeometry &geometry, Point point, const Point &position)
        {
            const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() *
                                                std::max({1.0, std::abs(double(point.X)),
                                                          std::abs(double(point.Z)),
                                                          std::abs(double(position.X)), std::abs(double(position.Z)),
                                                          std::abs(double(partBounds.XMin)), std::abs(double(partBounds.XMax)),
                                                          std::abs(double(partBounds.ZMin)), std::abs(double(partBounds.ZMax)),
                                                          std::abs(double(toolBounds.XMin)), std::abs(double(toolBounds.XMax)),
                                                          std::abs(double(toolBounds.ZMin)), std::abs(double(toolBounds.ZMax))});
            return std::max(0.0, double(geometry.unsignedDistance(point)) - numerical);
        };
        const auto collides = [&](const Point &position)
        {
            collisionRadius = 0;
            if (toolBounds.XMin + position.X > partBounds.XMax + resolution ||
                toolBounds.XMax + position.X < std::min(0.0f, partBounds.XMin) - resolution ||
                toolBounds.ZMin + position.Z > partBounds.ZMax + resolution ||
                toolBounds.ZMax + position.Z < partBounds.ZMin - resolution)
                return false;
            for (const auto &edge : toolGeometry.boundary)
            {
                const Point witness(edge.segment.start.X + position.X,
                                    edge.segment.start.Z + position.Z);
                if (partGeometry.isInside(witness))
                {
                    collisionRadius = interiorRadius(partGeometry, witness, position);
                    return true;
                }
            }
            for (const auto &edge : partGeometry.boundary)
            {
                const Point witness(edge.segment.start.X - position.X,
                                    edge.segment.start.Z - position.Z);
                if (toolGeometry.isInside(witness))
                {
                    collisionRadius = interiorRadius(toolGeometry, witness, position);
                    return true;
                }
            }
            try
            {
                partGeometry.validateToolSweep(toolGeometry, position, position);
            }
            catch (const std::runtime_error &)
            {
                return true;
            }
            return false;
        };
        const Point contact = tool.getRadialContactPoint();
        ZMin = stock.ZMin - contact.Z;
        Point start = Point(-toolBounds.XMin, partBounds.ZMax - contact.Z);

        if (partBounds.ZMax < stock.ZMax)
        {
            while (collides(start))
            {
                // move the tool along the z axis until it no longer intersects the part.
                start = start.add(Point(0, resolution));
            }

            start.Z += resolution;
            points.push_back(start);
        }

        // Reject steps lost to float rounding; a larger step could skip thin features //
        const auto advanceRadial = [&](float &x, float z)
        {
            const float next = x + resolution * 0.5;
            if (!(next > x))
                throw std::runtime_error("Cannot advance radial defeature scan at coordinate precision: origin (" +
                                         std::to_string(x) + ", " + std::to_string(z) +
                                         "), step " + std::to_string(resolution * 0.5));
            x = next;
        };

        float z_pos = start.Z;
        while (z_pos > ZMin)
        {
            float x_pos = -toolBounds.XMin;
            const float x_limit = partBounds.XMax - toolBounds.XMin + resolution;
            while (x_pos < x_limit)
            {
                Point iteration_position = Point(x_pos, z_pos);
                if (!collides(iteration_position))
                {
                    iteration_position.X += resolution * 0.25;

                    if (points.size() > 1 && allow_grooving == false)
                    {
                        float last_x = points.back().X;
                        if (iteration_position.X < last_x)
                            iteration_position.X = last_x;
                    }

                    if (collides(iteration_position))
                    {
                        advanceRadial(x_pos, z_pos);
                        continue;
                    }
                    points.push_back(iteration_position);
                    break;
                }
                const double previousX = x_pos;
                do
                {
                    advanceRadial(x_pos, z_pos);
                } while (x_pos < x_limit && double(x_pos) - previousX < collisionRadius);
            }

            z_pos -= resolution;
        }

        std::vector<Point> safePoints;
        for (const Point &point : points)
        {
            if (safePoints.empty())
            {
                partGeometry.validateToolSweep(toolGeometry, point, point);
                safePoints.push_back(point);
                continue;
            }
            const Point previous = safePoints.back();
            try
            {
                partGeometry.validateToolSweep(toolGeometry, previous, point);
                safePoints.push_back(point);
                continue;
            }
            catch (const std::runtime_error &)
            {
            }
            bool connected = false;
            for (const Point &corner : {Point(point.X, previous.Z), Point(previous.X, point.Z)})
            {
                try
                {
                    partGeometry.validateToolSweep(toolGeometry, previous, corner);
                    partGeometry.validateToolSweep(toolGeometry, corner, point);
                    safePoints.push_back(corner);
                    safePoints.push_back(point);
                    connected = true;
                    break;
                }
                catch (const std::runtime_error &)
                {
                }
            }
            if (!connected)
            {
                const float radial = std::max({partBounds.XMax - toolBounds.XMin,
                                               previous.X, point.X}) +
                                     resolution;
                const Point exit(radial, previous.Z);
                const Point entry(radial, point.Z);
                partGeometry.validateToolSweep(toolGeometry, previous, exit);
                partGeometry.validateToolSweep(toolGeometry, exit, entry);
                partGeometry.validateToolSweep(toolGeometry, entry, point);
                safePoints.push_back(exit);
                safePoints.push_back(entry);
                safePoints.push_back(point);
                connected = true;
            }
            if (!connected)
                throw std::runtime_error("Cannot construct a collision-free defeature connector");
        }

        std::vector<Point> defeatured_points;
        if (safePoints.size() < 2)
            throw std::runtime_error("Defeature produced fewer than two clear origins");
        defeatured_points.push_back(safePoints.front());
        const auto reduceSafe = [&](auto &&self, size_t first, size_t last) -> void
        {
            if (last == first + 1)
            {
                defeatured_points.push_back(safePoints[last]);
                return;
            }
            double maximum = 0;
            size_t split = (first + last) / 2;
            Segment chord(safePoints[first], safePoints[last]);
            for (size_t index = first + 1; index < last; ++index)
            {
                const double distance = chord.distanceToPoint(safePoints[index]);
                if (distance > maximum)
                {
                    maximum = distance;
                    if (maximum > resolution)
                        split = index;
                }
            }
            if (maximum <= resolution)
            {
                try
                {
                    partGeometry.validateToolSweep(toolGeometry, safePoints[first], safePoints[last]);
                    defeatured_points.push_back(safePoints[last]);
                    return;
                }
                catch (const std::runtime_error &)
                {
                }
            }
            self(self, first, split);
            self(self, split, last);
        };
        reduceSafe(reduceSafe, 0, safePoints.size() - 1);
        return this->fromPoints(defeatured_points);
    }

    void SegmentGroup::PreparedGeometry::validateToolSweepSpan(
        const PreparedGeometry &tool, Point start, Point end) const
    {
        // Certify insert clearance throughout a translation, rejecting collisions or unresolved sweeps //
        const double xmin = std::min(start.X, end.X) + double(tool.bounds.XMin);
        const double xmax = std::max(start.X, end.X) + double(tool.bounds.XMax);
        const double zmin = std::min(start.Z, end.Z) + double(tool.bounds.ZMin);
        const double zmax = std::max(start.Z, end.Z) + double(tool.bounds.ZMax);
        const double margin = 1e-5 + 4 * std::numeric_limits<float>::epsilon() *
            std::max({1.0, std::abs(xmin), std::abs(xmax), std::abs(zmin), std::abs(zmax),
                      std::abs(double(this->bounds.XMin)), std::abs(double(this->bounds.XMax)),
                      std::abs(double(this->bounds.ZMin)), std::abs(double(this->bounds.ZMax))});
        // Disjoint swept envelopes prove clearance even for long, near-tangent moves.
        if (xmin > this->bounds.XMax + margin || xmax < this->bounds.XMin - margin ||
            zmin > this->bounds.ZMax + margin || zmax < this->bounds.ZMin - margin)
            return;
        const auto &boundaryBounds = this->boundaryBounds;
        for (const auto &edge : this->boundary)
            if (tool.isInside(Point(edge.segment.start.X - start.X,
                                    edge.segment.start.Z - start.Z)))
                throw std::runtime_error("Turning insert contains part material at origin (" +
                                         std::to_string(start.X) + ", " + std::to_string(start.Z) +
                                         "), part vertex (" + std::to_string(edge.segment.start.X) +
                                         ", " + std::to_string(edge.segment.start.Z) + ")");

        double moveX = double(end.X) - start.X;
        double moveZ = double(end.Z) - start.Z;
        double travel = std::hypot(moveX, moveZ);
        size_t patches = 0;
        const auto validatePatch = [&](auto &&self, const PreparedSegment &edge,
                                       double edgeStart, double edgeEnd,
                                       double moveStart, double moveEnd) -> void
        {
            if (++patches > 8192)
                throw std::runtime_error("Cannot certify turning insert sweep within subdivision limit: move (" +
                                         std::to_string(start.X) + ", " + std::to_string(start.Z) + ") -> (" +
                                         std::to_string(end.X) + ", " + std::to_string(end.Z) + "), edge (" +
                                         std::to_string(edge.segment.start.X) + ", " + std::to_string(edge.segment.start.Z) + ") -> (" +
                                         std::to_string(edge.segment.end.X) + ", " + std::to_string(edge.segment.end.Z) + ")");
            const double alongEdge = (edgeStart + edgeEnd) / 2;
            const double alongMove = (moveStart + moveEnd) / 2;
            double localX, localZ, edgeReach, edgeXReach, edgeZReach;
            if (edge.segment.bulge == 0)
            {
                const double dx = double(edge.segment.end.X) - edge.segment.start.X;
                const double dz = double(edge.segment.end.Z) - edge.segment.start.Z;
                localX = edge.segment.start.X + alongEdge * dx;
                localZ = edge.segment.start.Z + alongEdge * dz;
                edgeReach = std::hypot(dx, dz) * (edgeEnd - edgeStart) / 2;
                edgeXReach = std::abs(dx) * (edgeEnd - edgeStart) / 2;
                edgeZReach = std::abs(dz) * (edgeEnd - edgeStart) / 2;
            }
            else
            {
                const double angle = edge.arc.startAngle + edge.arc.direction * edge.arc.sweep * alongEdge;
                localX = edge.arc.centre.X + edge.arc.radius * std::cos(angle);
                localZ = edge.arc.centre.Z + edge.arc.radius * std::sin(angle);
                edgeReach = edge.arc.radius * edge.arc.sweep * (edgeEnd - edgeStart) / 2;
                edgeXReach = edgeZReach = 0;
                const auto include = [&](double boundaryAngle)
                {
                    edgeXReach = std::max(edgeXReach, std::abs(edge.arc.centre.X +
                                                               edge.arc.radius * std::cos(boundaryAngle) - localX));
                    edgeZReach = std::max(edgeZReach, std::abs(edge.arc.centre.Z +
                                                               edge.arc.radius * std::sin(boundaryAngle) - localZ));
                };
                include(edge.arc.startAngle + edge.arc.direction * edge.arc.sweep * edgeStart);
                include(edge.arc.startAngle + edge.arc.direction * edge.arc.sweep * edgeEnd);
                const double pi = std::acos(-1.0);
                for (double extremum : {0.0, pi / 2, pi, 3 * pi / 2})
                {
                    double progress = std::fmod(edge.arc.direction *
                                                    (extremum - edge.arc.startAngle),
                                                2 * pi);
                    if (progress < 0)
                        progress += 2 * pi;
                    if (progress >= edge.arc.sweep * edgeStart && progress <= edge.arc.sweep * edgeEnd)
                        include(extremum);
                }
            }
            Point sample(localX + start.X + alongMove * moveX,
                         localZ + start.Z + alongMove * moveZ);
            const double numerical = 1e-5 + 4 * std::numeric_limits<float>::epsilon() *
                                                std::max({1.0, std::abs(double(sample.X)),
                                                          std::abs(double(sample.Z))});
            const double distance = this->sdv(sample);
            if (distance <= numerical)
                throw std::runtime_error("Cannot certify turning insert sweep clear of part material");
            const double moveReach = travel * (moveEnd - moveStart) / 2;
            if (distance > edgeReach + moveReach + numerical)
                return;
            const double xReach = edgeXReach + numerical +
                                  std::abs(moveX) * (moveEnd - moveStart) / 2;
            const double zReach = edgeZReach + numerical +
                                  std::abs(moveZ) * (moveEnd - moveStart) / 2;
            bool touchesBoundary = false;
            for (size_t index = 0; index < boundaryBounds.size(); ++index)
            {
                const auto &bounds = boundaryBounds[index];
                if (!(sample.X + xReach < bounds.XMin || sample.X - xReach > bounds.XMax ||
                      sample.Z + zReach < bounds.ZMin || sample.Z - zReach > bounds.ZMax))
                {
                    const auto &target = this->boundary[index];
                    if (target.segment.bulge != 0)
                    {
                        const double dx = std::abs(double(sample.X) - target.arc.centre.X);
                        const double dz = std::abs(double(sample.Z) - target.arc.centre.Z);
                        const double nearX = std::max(0.0, dx - xReach);
                        const double nearZ = std::max(0.0, dz - zReach);
                        const double nearest = std::hypot(nearX, nearZ);
                        const double farthest = std::hypot(dx + xReach, dz + zReach);
                        // A patch entirely inside or outside the supporting circle cannot cross its arc.
                        if (nearest > target.arc.radius + numerical ||
                            farthest < target.arc.radius - numerical)
                            continue;
                    }
                    touchesBoundary = true;
                    break;
                }
            }
            if (!touchesBoundary)
                return;
            if (alongEdge == edgeStart || alongEdge == edgeEnd ||
                alongMove == moveStart || alongMove == moveEnd)
                throw std::runtime_error("Cannot certify turning insert sweep at coordinate precision");
            if (edgeReach >= moveReach)
            {
                self(self, edge, edgeStart, alongEdge, moveStart, moveEnd);
                self(self, edge, alongEdge, edgeEnd, moveStart, moveEnd);
            }
            else
            {
                self(self, edge, edgeStart, edgeEnd, moveStart, alongMove);
                self(self, edge, edgeStart, edgeEnd, alongMove, moveEnd);
            }
        };
        for (size_t index = 0; index < tool.boundary.size(); ++index)
        {
            const auto &edge = tool.boundary[index];
            if (index >= tool.originalCount &&
                edge.segment.start.X == edge.segment.end.X &&
                edge.segment.start.Z == edge.segment.end.Z)
                continue;
            moveX = double(end.X) - start.X;
            moveZ = double(end.Z) - start.Z;
            travel = std::hypot(moveX, moveZ);
            const double dx = double(edge.segment.end.X) - edge.segment.start.X;
            const double dz = double(edge.segment.end.Z) - edge.segment.start.Z;
            const double lengthSquared = dx * dx + dz * dz;
            if (edge.segment.bulge == 0 && lengthSquared > 0 && dx * moveZ == dz * moveX)
            {
                const double shift = (dx * moveX + dz * moveZ) / lengthSquared;
                moveX = moveZ = travel = 0;
                validatePatch(validatePatch, edge, std::min(0.0, shift),
                              std::max(1.0, 1 + shift), 0, 1);
            }
            else
                validatePatch(validatePatch, edge, 0, 1, 0, 1);
        }
    }

    SegmentGroup SegmentGroup::fromPoints(std::vector<Point> points)
    {
        // Join consecutive points into an ordered group of straight segments //
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
        // Copy all segment endpoints and bulges into an independent group //
        SegmentGroup segmentGroup = SegmentGroup();

        for (auto &segment : this->segments)
        {
            Point start = Point(segment.start.X, segment.start.Z);
            Point end = Point(segment.end.X, segment.end.Z);
            segmentGroup.addSegment(Segment(start, end, segment.bulge));
        }

        return segmentGroup;
    }

    SegmentGroup SegmentGroup::reversed() const
    {
        SegmentGroup result;
        for (auto segment = segments.rbegin(); segment != segments.rend(); ++segment)
            result.addSegment(Segment(segment->end, segment->start, -segment->bulge));
        return result;
    }

    SegmentGroup SegmentGroup::reflectX(double radius) const
    {
        if (!std::isfinite(radius))
            throw std::invalid_argument("Radial reflection requires a finite reference radius");
        SegmentGroup result;
        for (const auto &segment : segments)
            result.addSegment(Segment(Point(radius - segment.start.X, segment.start.Z),
                                      Point(radius - segment.end.X, segment.end.Z),
                                      -segment.bulge));
        return result;
    }

    std::vector<Point> SegmentGroup::reduce(std::vector<Point> &points, float tolerance)
    {
        // Return a simplified polyline using the supplied distance tolerance //
        std::vector<Point> out;
        this->rdp(points, tolerance, out);
        return out;
    }

    void SegmentGroup::rdp(std::vector<Point> &points, float tolerance, std::vector<Point> &out)
    {
        // Simplify a polyline recursively with the Ramer-Douglas-Peucker algorithm //

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
        // Reserve a validation hook; no geometry checks are currently performed //

        // check each segment is connected

        // check that the group is open i.e, the start and end points are not connected

        // check that the start and end points are at x = 0 (only valid for the primary group / part shape)
    }

    std::array<Segment, 3> SegmentGroup::axisClosure()
    {
        // Build axis-closing edges, using direct closure for endpoints at the same Z //
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
            Segment(Point(0, end.Z), Point(0, start.Z))};
    }

    Point SegmentGroup::closestPoint(Point point, bool *onProfile)
    {
        // Find the nearest axis-closed boundary point and optionally identify original-profile hits //
        return this->prepareGeometry().closestPoint(point, onProfile);
    }

    SegmentGroup::PreparedGeometry SegmentGroup::prepareGeometry()
    {
        // Snapshot the profile, axis closures, arc data and complete boundary bounds //
        const auto closure = this->axisClosure();
        PreparedGeometry prepared;
        prepared.originalCount = this->segments.size();
        prepared.boundary.reserve(this->segments.size() + closure.size());
        for (const auto &segment : this->segments)
            prepared.boundary.emplace_back(segment);
        for (const auto &segment : closure)
            prepared.boundary.emplace_back(segment);
        prepared.bounds = prepared.boundary.front().segment.Boundbox();
        prepared.boundaryBounds.reserve(prepared.boundary.size());
        for (auto &edge : prepared.boundary)
        {
            const auto bounds = edge.segment.Boundbox();
            prepared.boundaryBounds.push_back(bounds);
            prepared.bounds.XMin = std::min(prepared.bounds.XMin, bounds.XMin);
            prepared.bounds.XMax = std::max(prepared.bounds.XMax, bounds.XMax);
            prepared.bounds.ZMin = std::min(prepared.bounds.ZMin, bounds.ZMin);
            prepared.bounds.ZMax = std::max(prepared.bounds.ZMax, bounds.ZMax);
        }
        prepared.containmentMargin = 4 * std::numeric_limits<float>::epsilon() *
                                     std::max({1.0f, std::abs(prepared.bounds.XMin), std::abs(prepared.bounds.XMax),
                                               std::abs(prepared.bounds.ZMin), std::abs(prepared.bounds.ZMax)});
        return prepared;
    }

    Point SegmentGroup::PreparedGeometry::closestPoint(Point point, bool *onProfile) const
    {
        // Find the nearest prepared boundary point, preferring original geometry on exact ties //
        if (!std::isfinite(point.X) || !std::isfinite(point.Z))
            throw std::invalid_argument("Query point must be finite");
        Point closest = this->boundary.front().segment.start;
        double closestDistance = std::numeric_limits<double>::infinity();
        bool closestOnProfile = true;
        auto consider = [&](const PreparedSegment &prepared, bool original)
        {
            Point pnt = prepared.segment.closestPointPrepared(point, prepared.arc);
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
        for (size_t i = 0; i < this->boundary.size(); ++i)
            consider(this->boundary[i], i < this->originalCount);
        if (onProfile != nullptr)
            *onProfile = closestOnProfile;
        return closest;
    }

    float SegmentGroup::sdv(Point point)
    {
        // Return signed distance to the axis-closed boundary, negative inside the region //
        return this->prepareGeometry().sdv(point);
    }

    float SegmentGroup::PreparedGeometry::unsignedDistance(Point point) const
    {
        // Return the shortest distance to the prepared boundary without classifying the point //
        return this->closestPoint(point).distanceTo(point);
    }

    float SegmentGroup::PreparedGeometry::sdv(Point point) const
    {
        // Apply the prepared region's inside or outside sign to its nearest-boundary distance //
        const float distance = this->unsignedDistance(point);
        return this->isInside(point) ? -distance : distance;
    }

    bool SegmentGroup::isInside(Point point)
    {
        // Classify a point against the axis-closed region, counting boundary points as inside //
        return this->prepareGeometry().isInside(point);
    }

    SegmentGroup::PreparedSegment::PreparedSegment(Segment source)
        : segment(source), arc(this->segment.prepareArc())
    {
        // Cache arc geometry and X-monotone intervals for vertical-ray crossing tests //
        if (segment.bulge == 0 ||
            (segment.start.X == segment.end.X && segment.start.Z == segment.end.Z))
            return;
        const double pi = std::acos(-1.0);
        std::array<std::pair<double, double>, 4> breaks;
        breaks[0] = {0, segment.start.X};
        breaks[1] = {arc.sweep, segment.end.X};
        size_t count = 2;
        for (double angle : {0.0, pi})
        {
            const double position = std::fmod(
                arc.direction * (angle - arc.startAngle) + 2 * pi, 2 * pi);
            if (position > 0 && position < arc.sweep)
                breaks[count++] = {position, arc.centre.X + (angle == 0 ? arc.radius : -arc.radius)};
        }
        std::sort(breaks.begin(), breaks.begin() + count);
        for (size_t i = 1; i < count; ++i)
        {
            const double middle = arc.startAngle + arc.direction *
                                                       (breaks[i - 1].first + breaks[i].first) / 2;
            intervals[intervalCount++] = {
                breaks[i - 1].second, breaks[i].second, std::sin(middle) > 0};
        }
    }

    int SegmentGroup::PreparedSegment::crossings(const Point &point) const
    {
        // Return -1 for a boundary point, otherwise count vertical-ray crossings above the query //
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

        const Point centre = arc.centre;
        const double radius = arc.radius;
        const double pi = std::acos(-1.0);
        const double direction = arc.direction;
        const double sweep = arc.sweep;
        const double startAngle = arc.startAngle;
        auto progress = [&](double angle)
        {
            return std::fmod(direction * (angle - startAngle) + 2 * pi, 2 * pi);
        };
        const double px = double(point.X) - centre.X;
        const double pz = double(point.Z) - centre.Z;
        const double epsilon = 4 * std::numeric_limits<float>::epsilon();
        if (std::abs(px * px + pz * pz - radius * radius) <=
                epsilon * radius * radius &&
            progress(std::atan2(pz, px)) <= sweep + epsilon)
            return -1;

        const double discriminant = radius * radius - px * px;
        if (discriminant < -epsilon * radius * radius)
            return 0;
        const double height = std::sqrt(std::max(0.0, discriminant));
        int result = 0;
        for (size_t i = 0; i < intervalCount; ++i)
        {
            const auto &interval = intervals[i];
            if ((interval.startX > point.X) == (interval.endX > point.X))
                continue;
            const double z = centre.Z + (interval.positiveZ ? height : -height);
            if (z > point.Z)
                ++result;
        }
        return result;
    }

    bool SegmentGroup::PreparedGeometry::isInside(Point point) const
    {
        // Reject points outside the bounds, then classify by ray parity with boundary inclusion //
        const float margin = this->containmentMargin;
        if (point.X < bounds.XMin - margin || point.X > bounds.XMax + margin ||
            point.Z < bounds.ZMin - margin || point.Z > bounds.ZMax + margin)
            return false;
        int intersections = 0;
        for (const auto &segment : this->boundary)
        {
            const int count = segment.crossings(point);
            if (count < 0)
                return true;
            intersections += count;
        }
        return intersections % 2 != 0;
    }

}
