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

    this->segmentGroup = segmentgroup;

    // check width and height are the same
    // TODO: remove the width and height if they need to match
    if (width != height)
    {
        throw std::runtime_error("quadtree width and height must match");
    }
    // create the base node
    int depth = 0;
    Node bn = {center, width, height, depth};
    this->basenode = bn;

    // set the precision
    this->precision = 0.2;
}

std::vector<Point> Quadtree::getOffset(float offsetValue)
{
    // return the points that represent the calculated offset //
    this->offset = offsetValue;
    // start to process the quadtree, populating the offsetBoundaryPoints
    this->conquer(this->basenode);
    // sort the points so they can be used to build a tool path
    return this->sortPoints(segmentGroup->getSegments()[0].start, this->offsetBoundaryPoints);
}

void Quadtree::conquer(Node &node)
{
    // Recursively divide each node until the target precision is reached //

    // get the nodes signed distance value
    // representing the distance from the closest point on the segmentGroup
    // negative values are inside the segmentGroup
    // positive values are outside the segmentGroup
    node.sdv = this->segmentGroup->sdv(node.center);

    // check if it is possible that this node contains the target offset
    if (this->nodeCouldContain(this->offset, node))
    {
        // check if we have reached the desired precision
        if ((node.width <= this->precision))
        {
            // check that the signed distance value is the same sign as the requested offset
            if (std::signbit(node.sdv) == std::signbit(this->offset))
            {
                // get the closest point on the segmentGroup
                Point closest = this->segmentGroup->closestPoint(node.center);
                // get the projected boundary point
                Point projectedPoint = closest.project(closest.angleTo(node.center), abs(this->offset));

                // check if projected point is inside the node
                if (this->insideNode(projectedPoint, node))
                {
                    Point segmentStart = segmentGroup->getSegments()[0].start;
                    // only collect points inside the segment boundary
                    if (projectedPoint.Z <= segmentStart.Z)
                    {
                        this->offsetBoundaryPoints.push_back(projectedPoint);
                    }
                }
            }

            return;
        }
        else
        {
            this->divide(node);
        }
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
    // check if the target offset could be within the node//

    // get the distance from the node center to a corner of the node
    // Based on pythagoras theorem: A^2 + B^2 = C^2; assumes the node is square
    // This is a quick check and could include false positives
    float cornerDistance = sqrt(pow(node.width, 2) * 2) * 0.5;

    if (node.sdv - cornerDistance <= offset && node.sdv + cornerDistance >= offset)
    {
        return true;
    }

    return false;
}

bool Quadtree::insideNode(Point &point, Node &node)
{
    // determine if point is inside node //
    float nodeXMin = node.center.X - node.height * 0.5;
    float nodeXMax = node.center.X + node.height * 0.5;
    float nodeZMin = node.center.Z - node.width * 0.5;
    float nodeZMax = node.center.Z + node.width * 0.5;

    // point is inside if it lies on the min boundary of node
    if (point.X >= nodeXMin && point.X < nodeXMax)
    {
        if (point.Z >= nodeZMin && point.Z < nodeZMax)
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

std::vector<Point> Quadtree::query(Node &node, std::vector<Point> &offsetBoundaryPoints)
{
    // Find the points in the quadtree that are close to target value //

    float dist = node.sdv;
    if (dist - this->precision * 0.5 >= this->offset && dist + this->precision * 0.5 <= this->offset)
    {
        offsetBoundaryPoints.push_back(node.center);
    }

    if (node.divided)
    {
        for (auto &child : node.child_nodes)
        {
            this->query(child, offsetBoundaryPoints);
        }
    }

    return offsetBoundaryPoints;
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
