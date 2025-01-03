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
    float width;
    float height;
    int depth;
    bool divided;
    float sdv;
    std::vector<Node> child_nodes;
    Node(Point center, float width, float height, int depth) : center(center), width(width), height(height), depth(depth) {}
    Node() {}
};

// forward declaration for segment group
class SegmentGroup;

class Quadtree
{
public:
    Quadtree();
    ~Quadtree();

    void initialise(SegmentGroup *segmentgroup, Point center, float width, float height);
    std::vector<Point> getOffset(float offset_value);
    std::vector<Node> getNodes();

private:
    float offset;

    SegmentGroup *segment_group;
    Node basenode;

    void divide(Node &);
    void conquer(Node &);
    std::vector<Point> query(Node &node, std::vector<Point> &found_points);
    std::vector<Node> queryNodes(Node &node, std::vector<Node> &nodes);
    bool nodeCouldContain(float offset, Node &node);
    std::vector<Point> sortPoints(Point datum, std::vector<Point> &points);
};

#endif