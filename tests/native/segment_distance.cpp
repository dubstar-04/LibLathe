// From the repository root, compile and run:
// g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer
//   -I liblathe/base tests/native/segment_distance.cpp
//   liblathe/base/{quadtree,segmentgroup,segment,boundbox,point}.cpp
//   -o /tmp/liblathe-segment-distance
// ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/liblathe-segment-distance
#include <cmath>
#include <iostream>
#include <stdexcept>

#include "segmentgroup.h"

void check(Segment segment, Point query, Point expected, float expectedDistance)
{
    Point closest = segment.closestPoint(query);
    float distance = segment.distanceToPoint(query);
    if (!std::isfinite(closest.X) || !std::isfinite(closest.Z) ||
        !std::isfinite(distance) || closest.distanceTo(expected) > 0.00001f ||
        std::abs(distance - expectedDistance) > 0.00001f ||
        distance != query.distanceTo(closest))
        throw std::runtime_error("Finite segment distance or closest point is incorrect");
}

int main()
{
    for (float direction : {-1.0f, 1.0f})
    {
        SegmentGroup group;
        group.addSegment(Segment(Point(0, 0), Point(2, 0), direction));
        group.addSegment(Segment(Point(2, 0), Point(0, 0)));
        for (float z : {-1.0f, 0.75f})
        {
            Point query(1, z * direction);
            Point expected(1, z < 0 ? 0 : direction);
            float expectedDistance = z < 0 ? 1 : -0.25f;
            if (group.closestPoint(query).distanceTo(expected) > 0.00001f ||
                std::abs(group.sdv(query) - expectedDistance) > 0.00001f)
                throw std::runtime_error("Group distance and closest point disagree");
        }
        for (bool reverse : {false, true})
        {
            Point start = reverse ? Point(2, 0) : Point(0, 0);
            Point end = reverse ? Point(0, 0) : Point(2, 0);
            Segment arc(start, end, reverse ? -direction : direction);
            check(arc, Point(1, direction), Point(1, direction), 0);
            check(arc, Point(1, 2 * direction), Point(1, direction), 1);
            check(arc, Point(-1, -direction), Point(0, 0), std::sqrt(2.0f));
            check(arc, Point(3, -direction), Point(2, 0), std::sqrt(2.0f));
            check(arc, Point(1, -direction), start, std::sqrt(2.0f));
            check(arc, Point(1, 0), start, 1);
            check(arc, start, start, 0);
            check(arc, end, end, 0);
        }
    }

    float rootTwo = std::sqrt(2.0f);
    Segment major(Point(0, 0), Point(2, 0), std::tan(3 * std::acos(-1.0) / 8));
    check(major, Point(1, 1 + rootTwo), Point(1, 1 + rootTwo), 0);
    check(major, Point(1, -1), Point(0, 0), rootTwo);
    check(major, Point(1, 1), Point(0, 0), rootTwo);
    check(Segment(Point(1, 2), Point(4, 2)), Point(1, 3), Point(1, 2), 1);
    for (float bulge : {0.0f, -1.0f, 1.0f})
        check(Segment(Point(1, 2), Point(1, 2), bulge),
              Point(4, 6), Point(1, 2), 5);
    std::cout << "Finite line and arc distances and closest points passed\n";
}
