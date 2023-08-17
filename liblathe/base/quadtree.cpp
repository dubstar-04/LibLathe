#include "quadtree.h"
#include <iostream>
#include<limits>

Quadtree::Quadtree() 
{
}

Quadtree::~Quadtree() {}

void Quadtree::add_base_node(Point center, float width, float height) 
{
    int depth = 0;
    Node bn = {center, width, height, depth};
    this->basenode = bn;
    this->conquer(this->basenode);
}

void Quadtree::conquer(Node &node){
    // Divide each node until the target precision is reached
    
    node.sdv = this->sdv(node.center);

    if (node.depth >= 11){
        return;
    }

    float stepover = 0.25;

    if(node.sdv >= stepover && node.sdv <= stepover + 0.005){
        return;
    }

    if (node.depth < 5  || this->node_could_contain(stepover, node)){
        this->divide(node);
    }
}


void Quadtree::divide(Node &node){
    // Divide (branch) this node by spawning four children nodes 

    // std::cout << "Divide:" << node.depth << "\n";

    float cx = node.center.x;
    float cy = node.center.z;
    float w = node.width / 2;
    float h = node.height / 2;
    int depth = node.depth + 1; 

    float x = cx - h/2;
    float z = cy + w/2;
    Point pne = {x, z};
    Node ne = {pne, w, h, depth};

    x = cx + h/2;
    z = cy + w/2;
    Point pse = {x, z};
    Node se = {pse, w, h, depth};

    x = cx + h/2;
    z = cy - w/2;
    Point psw = {x, z};
    Node sw = {psw, w, h, depth};

    x = cx - h/2;
    z = cy - w/2;
    Point pnw = {x, z};
    Node nw = {pnw, w, h, depth};

    node.child_nodes.push_back(ne);
    node.child_nodes.push_back(se);
    node.child_nodes.push_back(sw);
    node.child_nodes.push_back(nw);

    node.divided = true;

    // std::cout << "Divided" << node.divided << "\n";
    // std::cout << "Children:" << node.child_nodes.size() << "\n";

    for (auto &child : node.child_nodes)
    {  
        this->conquer(child);
    }
}

bool Quadtree::node_could_contain(float offset, Node &node){

    if(node.sdv - node.height / 2 <= offset && node.sdv + node.height / 2 >= offset){
        return true;
    }

    if(node.sdv - node.width / 2 <= offset && node.sdv + node.width / 2 >= offset){
        return true;
    }

    return false;

}


std::vector<Point> Quadtree::get_offset(float target){
    std::vector<Point> found_points;
    return this->query(this->basenode, target, found_points);
}

std::vector<Point> Quadtree::query(Node &node, float target, std::vector<Point> &found_points){
    // Find the points in the quadtree that are close to target value 

    float dist = node.sdv;
    //std::cout << "query" << dist << "\n";
    if (dist >= target && dist <= target + 0.0075){
        // std::cout << "Point match" << dist << "\n";
        found_points.push_back(node.center);
    }

    //std::cout << "query divided: " << node.divided << "\n";
    if(node.divided){
        for (auto &child : node.child_nodes)
            {  
                this->query(child, target, found_points);
            }
    }

    return found_points;
}

std::vector<Node> Quadtree::get_nodes(){
    std::vector<Node> nodes;
    return this->query_nodes(this->basenode, nodes);
}

std::vector<Node> Quadtree::query_nodes(Node &node, std::vector<Node> &nodes){

    nodes.push_back(node);

    if(node.divided){
        for (auto &child : node.child_nodes)
            {  
                this->query_nodes(child, nodes);
            }
    }

    return nodes;
}

float Quadtree::sdv(Point point)
{   
    float x_min = 0.0; //StockBoundingBox.x_min;
    float x_max = 25.0; //StockBoundingBox.x_max;

    float z_min = -60.0; //StockBoundingBox.z_min;
    float z_max = 25.0; //StockBoundingBox.z_max;

    //std::vector<std::vector<float>> sdf;
    float sdv;

    bool inside = this->isInside(point);
    float dist_clst_pnt = std::numeric_limits<float>::infinity(); 

    // find closest point on the segment
    for (int i = 1; i < this->points.size(); i++) {
        Segment seg = {this->points[i-1], this->points[i]};
        Point clst = this->closest(point, seg.start, seg.end);
        float clst_dist = this->distance_to(point, clst);
        dist_clst_pnt = std::min(clst_dist, dist_clst_pnt);
    }

    sdv = abs(dist_clst_pnt);
    if (inside){
        sdv = -sdv;
    }

    return sdv;
}

void Quadtree::add_point(float x, float z){
    this->points.push_back({x, z});
}

int Quadtree::point_count(){
    return this->points.size();
}

float Quadtree::distance_to(Point a, Point b){
    return sqrt((a.x- b.x) * (a.x- b.x) + (a.z - b.z) * (a.z - b.z));

}

Point Quadtree::closest(Point point, Point start, Point end){

    float APx = point.x - start.x;
    float APy = point.z - start.z;
    float ABx = end.x - start.x;
    float ABy = end.z  - start.z;

    float magAB2 = ABx * ABx + ABy * ABy;
    float ABdotAP = ABx * APx + ABy * APy;
    float t = ABdotAP / magAB2;

    // check if the point is < start or > end
    if (t > 0.0 && t < 1.0){
        float x = start.x + ABx * t;
        float z = start.z + ABy * t;
        Point p = {x, z};
        return p; 
    }
    
    if (t < 0){
        return start;
    }
    //if (t > 1){
        return end;
    //}
}

int Quadtree::intersect(Segment a, Segment b){

    Point a1 = a.start;
    Point a2 = a.end;
    Point b1 = b.start;
    Point b2 = b.end;
    bool intersect = false;
    std::vector<Point> pts;

    float ua_t = (b2.x - b1.x) * (a1.z - b1.z) - (b2.z - b1.z) * (a1.x - b1.x);
    float ub_t = (a2.x - a1.x) * (a1.z - b1.z) - (a2.z - a1.z) * (a1.x - b1.x);
    float u_b = (b2.z - b1.z) * (a2.x - a1.x) - (b2.x - b1.x) * (a2.z - a1.z);

    if (u_b == 0){
        return 0;
    }

    float ua = ua_t / u_b;
    float ub = ub_t / u_b;

    if ((0 <= ua and ua <= 1) && (0 <= ub and ub <= 1)){
        float x = a1.x + ua * (a2.x - a1.x);
        float z = a1.z + ua * (a2.z - a1.z);
        Point pt = {x, z};
        pts.push_back(pt);
    }

    return pts.size();

}

bool Quadtree::isInside(Point point){
    int intersections = 0;

    // generate a ray to perform the crossing
    float x = point.x;
    float z = point.z + 150;
    Point plstart = {x, z};
    Segment projection_line = {plstart, point};
    
    for (int i = 1; i < this->points.size(); i++) {
        
        //// std::cout << "Intersect point" << i << "\n";
        
        Segment seg = {this->points[i-1], this->points[i]};
        
        // stop checking once past the point of interest
        if (seg.start.z < point.z)
        {
            break;
        }

        //if (round(seg.start.x, 5) <= round(point.x, 5) and round(seg.end.x, 5) <= round(point.x, 5)){
        //    continue;
        //}
            
        int intersect_pnts = this->intersect(projection_line, seg);
        intersections += intersect_pnts;
    }

    if (intersections % 2 == 0 && intersections > 0 || intersections == 0){
        //even
        return false;
    }

    //odd
    return true;
}
