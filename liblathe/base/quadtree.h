#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <vector>


#ifndef Quadtree_H
#define Quadtree_H

struct Point {
    Point(float &x, float &z) : x(x), z(z){ }
    float x;
    float z;
    Point(){}
};

struct Segment {
    Point start;
    Point end;
};

struct Node {
    Point center;
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
        float distance_to(Point, Point);
        Point closest(Point, Point, Point);
        Node basenode;

        void divide(Node&);
        void conquer(Node&);
        float sdv(Point);
        std::vector<Point> query(Node& node, float target, std::vector<Point>& found_points);
        std::vector<Node> query_nodes(Node& node, std::vector<Node>& nodes);
        bool node_could_contain(float offset, Node& node);
        
};



namespace py = pybind11;

PYBIND11_MODULE(quadtree, m) {
    // optional module docstring
    m.doc() = "Signed Distance Field";

    // bindings to Quadtree class
    py::class_<Quadtree>(m, "Quadtree")
        .def(py::init<>())
        .def("add_point", &Quadtree::add_point)
        .def("point_count", &Quadtree::point_count)
        .def("add_base_node", &Quadtree::add_base_node)
        .def("get_offset", &Quadtree::get_offset)
        .def("get_nodes", &Quadtree::get_nodes);

    // binding to the point struct
    py::class_<Point>(m, "Point")
        .def(py::init<float&, float&>())
        .def_readwrite("x", &Point::x)
        .def_readwrite("z", &Point::z);

    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("center", &Node::center)
        .def_readwrite("width", &Node::width)
        .def_readwrite("height", &Node::height)
        .def_readwrite("sdv", &Node::sdv);
}

#endif