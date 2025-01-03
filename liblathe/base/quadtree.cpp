#include <iostream>
#include <limits>

#include "quadtree.h"

Quadtree::Quadtree()
{
}

Quadtree::~Quadtree() {}

void Quadtree::initialise(SegmentGroup *segmentgroup, Point center, float width, float height)
{
    // Initialise the quadtree //
    // depth is the current node depth
    // basenode the the primary tree node

    this->segment_group = segmentgroup;
    int depth = 0;
    Node bn = {center, width, height, depth};
    this->basenode = bn;
}

std::vector<Point> Quadtree::getOffset(float offset_value)
{
    // return the points that represent the calculated offset //
    this->offset = offset_value;
    this->conquer(this->basenode);
    std::vector<Point> found_points;
    std::vector<Point> point = this->query(this->basenode, found_points);
    return this->sortPoints(segment_group->getSegments()[0].start, found_points);
}

void Quadtree::conquer(Node &node)
{
    // Divide each node until the target precision is reached

    node.sdv = this->segment_group->sdv(node.center);

    if (node.depth >= 11)
    {
        return;
    }

    if (node.sdv >= this->offset && node.sdv <= this->offset + 0.005)
    {
        return;
    }

    if (node.depth < 5 || this->nodeCouldContain(this->offset, node))
    {
        this->divide(node);
    }
}

void Quadtree::divide(Node &node)
{
    // Divide this node by creating four child nodes //

    float cx = node.center.X;
    float cy = node.center.Z;
    float w = node.width / 2;
    float h = node.height / 2;
    int depth = node.depth + 1;

    float x = cx - h / 2;
    float z = cy + w / 2;
    Point pne = Point(x, z);
    Node ne = {pne, w, h, depth};

    x = cx + h / 2;
    z = cy + w / 2;
    Point pse = Point(x, z);
    Node se = {pse, w, h, depth};

    x = cx + h / 2;
    z = cy - w / 2;
    Point psw = Point(x, z);
    Node sw = {psw, w, h, depth};

    x = cx - h / 2;
    z = cy - w / 2;
    Point pnw = Point(x, z);
    Node nw = {pnw, w, h, depth};

    node.child_nodes.push_back(ne);
    node.child_nodes.push_back(se);
    node.child_nodes.push_back(sw);
    node.child_nodes.push_back(nw);

    node.divided = true;

    for (auto &child : node.child_nodes)
    {
        this->conquer(child);
    }
}

bool Quadtree::nodeCouldContain(float offset, Node &node)
{
    // check if the node could contain an a point at offset distance from the segments //
    if (node.sdv - node.height / 2 <= offset && node.sdv + node.height / 2 >= offset)
    {
        return true;
    }

    if (node.sdv - node.width / 2 <= offset && node.sdv + node.width / 2 >= offset)
    {
        return true;
    }

    return false;
}

std::vector<Point> Quadtree::sortPoints(Point datum, std::vector<Point> &points)
{
    // sort the point set into a ordered set of points starting from datum //
    std::vector<Point> sorted_points;
    int point_count = points.size();
    Point target = datum;
    int closest_index;

    int input_point_count = points.size();

    while (points.size() != 0)
    {
        float dist = std::numeric_limits<float>::infinity();
        int index = 0;

        for (index; index < points.size(); index++)
        {
            // find closest point
            float target_to_point = target.distanceTo(points[index]);

            if (target_to_point < dist)
            {
                closest_index = index;
                dist = target_to_point;
            }
        }

        // add closest point to sorted points
        sorted_points.push_back(Point(points[closest_index].X, points[closest_index].Z));
        // remove point from points array
        points.erase(points.begin() + closest_index);
        // set target to last found point
        target = sorted_points.back();
    }

    if (input_point_count != sorted_points.size())
    {
        throw std::runtime_error("Quadtree error when ordering offset points");
    }
    return sorted_points;
}

std::vector<Point> Quadtree::query(Node &node, std::vector<Point> &found_points)
{
    // Find the points in the quadtree that are close to target value //

    float dist = node.sdv;
    if (dist >= this->offset && dist <= this->offset + 0.0075)
    {
        found_points.push_back(node.center);
    }

    if (node.divided)
    {
        for (auto &child : node.child_nodes)
        {
            this->query(child, found_points);
        }
    }

    return found_points;
}

std::vector<Node> Quadtree::getNodes()
{
    // return list of nodes //
    std::vector<Node> nodes;
    return this->queryNodes(this->basenode, nodes);
}

std::vector<Node> Quadtree::queryNodes(Node &node, std::vector<Node> &nodes)
{
    // build list of nodes //
    nodes.push_back(node);

    if (node.divided)
    {
        for (auto &child : node.child_nodes)
        {
            this->queryNodes(child, nodes);
        }
    }

    return nodes;
}
