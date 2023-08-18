#include <vector>
#include <math.h>

#include "point.h"

#ifndef Quadtree_H
#define Quadtree_H

struct Segment {
    Point start;
    Point end;
};

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


class Quadtree
{
    public:
        Quadtree();
        ~Quadtree();

        void add_point(float, float);
        int point_count();
        void add_base_node(Point center, float width, float height);
        std::vector<Point> get_offset(float target);
        std::vector<Node> get_nodes();
        
    private:
        std::vector<Point> points;
        bool isInside(Point);
        int intersect(Segment, Segment);
        Point closest(Point, Point, Point);
        Node basenode;

        void divide(Node&);
        void conquer(Node&);
        float sdv(Point);
        std::vector<Point> query(Node& node, float target, std::vector<Point>& found_points);
        std::vector<Node> query_nodes(Node& node, std::vector<Node>& nodes);
        bool node_could_contain(float offset, Node& node);
        
};

#endif