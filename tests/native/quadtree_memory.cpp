// Optional native memory diagnostic, not part of the required Python test suite.
// From the repository root:
// g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer
//   -I liblathe/base tests/native/quadtree_memory.cpp
//   liblathe/base/{quadtree,segmentgroup,segment,boundbox,point}.cpp
//   -o /tmp/liblathe-quadtree-memory
// ASAN_OPTIONS=detect_leaks=1 /tmp/liblathe-quadtree-memory
// For glibc heap accounting, compile without sanitizers and run with --heap-check.
#include <iostream>
#include <stdexcept>
#include <string>

#ifdef __GLIBC__
#include <malloc.h>
#endif

#include "quadtree.h"

void require(bool condition, const char *message)
{
    if (!condition)
        throw std::runtime_error(message);
}

void checkNode(const Node &node)
{
    require(!node.divided && node.sdv == 0 && node.child_nodes.empty(),
            "Node transient state is not initialised");
}

int main(int argc, char **argv)
{
    Node empty;
    checkNode(empty);
    require(empty.width == 0 && empty.height == 0 && empty.depth == 0,
            "Default node dimensions or depth are not initialised");
    Node sized(Point(4, 0), 8, 8, 0);
    checkNode(sized);

    SegmentGroup group;
    group.addSegment(Segment(Point(0, 0), Point(2, 0)));
    group.addSegment(Segment(Point(2, 0), Point(2, -4)));
    group.addSegment(Segment(Point(2, -4), Point(0, -4)));

    const bool heapCheck = argc == 2 && std::string(argv[1]) == "--heap-check";
#ifndef __GLIBC__
    require(!heapCheck, "Heap accounting requires glibc; run sanitizers instead");
#endif
    Quadtree tree;
    tree.initialise(&group, Point(4, 0), 8, 8);
    const auto expected = tree.getOffset(1);
    require(expected.size() == 32, "Unexpected reference point count");
    const auto expectedNodes = tree.getNodes().size();
    size_t heapBaseline = 0;
    for (int i = 0; i < 100; ++i)
    {
        {
            const auto points = tree.getOffset(1);
            require(points.size() == expected.size(), "Repeated offsets grow points");
            for (size_t j = 0; j < points.size(); ++j)
                require(points[j].X == expected[j].X && points[j].Z == expected[j].Z,
                        "Repeated offsets change coordinates");
            require(tree.getNodes().size() == expectedNodes, "Repeated offsets grow nodes");
        }
#ifdef __GLIBC__
        if (heapCheck)
        {
            const size_t liveHeap = mallinfo2().uordblks;
            // Warm up allocator caches before comparing equivalent calls.
            if (i == 9)
                heapBaseline = liveHeap;
            if (i > 9)
                require(liveHeap == heapBaseline, "Live heap grows between equivalent calls");
        }
#endif
    }
    for (int i = 0; i < 100; ++i)
    {
        tree.initialise(&group, Point(4, 0), 8, 8);
        require(tree.getOffset(1).size() == 32, "Reinitialisation changes point count");
    }
    std::cout << "Repeated offsets and reinitialisation passed";
    if (heapCheck)
        std::cout << "; stable live heap: " << heapBaseline << " bytes";
    std::cout << '\n';
}
