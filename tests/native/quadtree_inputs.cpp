// From the repository root, compile and run:
// g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer
//   -I liblathe/base tests/native/quadtree_inputs.cpp
//   liblathe/base/{quadtree,segmentgroup,segment,boundbox,point}.cpp
//   -o /tmp/liblathe-quadtree-inputs
// ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/liblathe-quadtree-inputs
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

#include "quadtree.h"

template <typename Exception, typename Function>
void expectException(Function function)
{
    try
    {
        function();
    }
    catch (const Exception &)
    {
        return;
    }
    throw std::runtime_error("Expected exception was not raised");
}

void require(bool condition, const char *message)
{
    if (!condition)
        throw std::runtime_error(message);
}

int main()
{
    Quadtree tree;
    expectException<std::runtime_error>([&] { tree.getOffset(1); });
    expectException<std::invalid_argument>([&] {
        tree.initialise(nullptr, Point(4, 0), 8, 8);
    });
    expectException<std::runtime_error>([&] { tree.getOffset(1); });

    SegmentGroup group;
    group.addSegment(Segment(Point(0, 0), Point(2, 0)));
    group.addSegment(Segment(Point(2, 0), Point(2, -4)));
    group.addSegment(Segment(Point(2, -4), Point(0, -4)));
    tree.initialise(&group, Point(4, 0), 8, 8);
    const auto expected = tree.getOffset(1);
    auto checkRecovery = [&] {
        const auto actual = tree.getOffset(1);
        require(actual.size() == expected.size(), "Rejected input changed point count");
        for (size_t i = 0; i < actual.size(); ++i)
            require(actual[i].X == expected[i].X && actual[i].Z == expected[i].Z,
                    "Rejected input changed coordinates");
    };
    SegmentGroup replacement;
    replacement.addSegment(Segment(Point(0, 0), Point(1, -1)));
    const float infinity = std::numeric_limits<float>::infinity();
    const float nan = std::numeric_limits<float>::quiet_NaN();
    for (float invalid : {0.0f, -1.0f, infinity, -infinity, nan})
    {
        expectException<std::invalid_argument>([&] {
            tree.initialise(&replacement, Point(4, 0), invalid, 8);
        });
        checkRecovery();
        expectException<std::invalid_argument>([&] {
            tree.initialise(&replacement, Point(4, 0), 8, invalid);
        });
        checkRecovery();
    }
    for (float invalid : {infinity, -infinity, nan})
    {
        expectException<std::invalid_argument>([&] {
            tree.initialise(&replacement, Point(invalid, 0), 8, 8);
        });
        checkRecovery();
        expectException<std::invalid_argument>([&] {
            tree.initialise(&replacement, Point(4, invalid), 8, 8);
        });
        checkRecovery();
        expectException<std::invalid_argument>([&] { tree.getOffset(invalid); });
        checkRecovery();
    }
    expectException<std::invalid_argument>([&] {
        tree.initialise(nullptr, Point(4, 0), 8, 8);
    });
    checkRecovery();
    expectException<std::invalid_argument>([&] {
        tree.initialise(&replacement, Point(4, 0), 8, 4);
    });
    checkRecovery();
    require(tree.getOffset(100).empty(), "Expected an empty contour");
    checkRecovery();
    require(!tree.getOffset(0).empty(), "Zero offset must remain supported");
    require(!tree.getOffset(-0.1f).empty(), "Negative offset must remain supported");

    SegmentGroup empty;
    tree.initialise(&empty, Point(4, 0), 8, 8);
    expectException<std::invalid_argument>([&] { tree.getOffset(1); });
    std::cout << "Invalid inputs, preserved state and recovery passed\n";
}
