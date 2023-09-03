#ifndef Quadtree_H
#define Quadtree_H

#include <vector>
#include <math.h>

#include "point.h"
#include "segment.h"
#include "segmentgroup.h"



struct Node {
    Point center = Point(0,0);
    float width;
    float height;
    int depth;
    bool divided;
    float sdv;
    std::vector<Node> child_nodes;
    Node(Point center, float width, float height, int depth) : center(center), width(width), height(height), depth(depth){ }
    Node(){}
};

// forward declaration for segment group
class SegmentGroup;

class Quadtree
{
    public:
        Quadtree();
        ~Quadtree();

        // void add_segments(std::vector<Segment> &segments);
        void initialise(SegmentGroup *segmentgroup, Point center, float width, float height);
        //void add_base_node(Point center, float width, float height);
        std::vector<Point> get_offset(float offset_value);
        std::vector<Node> get_nodes();
        
    private:
        float offset;

        SegmentGroup *segment_group;

        //std::vector<Segment> segments;

        //bool isInside(Point);
        Node basenode;

        void divide(Node&);
        void conquer(Node&);
        //float sdv(Point);
        std::vector<Point> query(Node& node, std::vector<Point>& found_points);
        std::vector<Node> query_nodes(Node& node, std::vector<Node>& nodes);
        bool node_could_contain(float offset, Node& node);

        std::vector<Point> sort_points(Point datum, std::vector<Point> &points);
        
};

#endif