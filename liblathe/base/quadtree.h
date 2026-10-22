#ifndef Quadtree_H
#define Quadtree_H

#include <vector>
#include <math.h>

#include "point.h"
#include "segment.h"
#include "segmentgroup.h"

struct Node
{
    Point center = Point(0, 0);
    float width = 0;
    float height = 0;
    int depth = 0;
    bool divided = false;
    float sdv = 0;
    std::vector<Node> child_nodes;
    Node(Point center, float width, float height, int depth) : center(center), width(width), height(height), depth(depth) {}
    Node() {}
};

// forward declaration for segment group
class SegmentGroup;

class Quadtree
{
public:
    static constexpr float defaultPrecision = 0.2f;

    Quadtree();
    ~Quadtree();

    // C++ callers own the geometry; it must outlive its use by this tree.
    // Python retains all groups supplied to initialise until the tree is destroyed.
    // Invalid geometry pointers or root bounds throw invalid_argument without changing state.
    void initialise(SegmentGroup *segmentgroup, Point center, float width, float height);
    // Throws runtime_error before initialisation, invalid_argument for empty geometry
    // or nonfinite offsets. A valid request with no contour returns an empty vector.
    // Uses the axis-closed field, but excludes artificial-closure candidates.
    // Original faces remain eligible; the first segment's start-Z clip is retained.
    // Zero levels sample both sides. Candidates must converge to the requested
    // level within float/arc-rounding precision; this does not bound connecting chords.
    std::vector<Point> getOffset(float offsetValue);
    std::vector<Node> getNodes();

private:
    // value to offset the segmentgroup by
    float offset = 0;
    // precision of the quadtree
    float precision = defaultPrecision;

    SegmentGroup *segmentGroup = nullptr;
    bool initialised = false;
    Node basenode;

    std::vector<Point> offsetBoundaryPoints;

    void divide(Node &);
    void conquer(Node &);
    bool projectToOffset(const Node &node, Point &point);
    std::vector<Point> query(Node &node, std::vector<Point> &offsetBoundaryPoints);
    std::vector<Node> queryNodes(Node &node, std::vector<Node> &nodes);
    bool nodeCouldContain(float offset, Node &node);
    bool insideNode(Point &point, Node &node);
    std::vector<Point> sortPoints(Point datum, std::vector<Point> &points);
};

#endif