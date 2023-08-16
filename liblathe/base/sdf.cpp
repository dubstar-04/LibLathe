#include "sdf.h"
#include <iostream>
#include<limits>


SDF::SDF() 
{   

}

SDF::~SDF() {}

std::vector<std::vector<float>> SDF::generate()
{   
    /*
    float x = 5.0;
    float z = 1.0;
    Point p = {x, z};
    bool inside = this->isInside(p);

    if(inside){
        std::cout << "I'm in" << std::endl;
    }else{
        std::cout << "I'm out" << std::endl;
    }
    */

    //  create a 2D SDF for the part geometry
    float resolution = 0.1;
    float x_min = 0.0; //StockBoundingBox.x_min;
    float x_max = 25.0; //StockBoundingBox.x_max;

    float z_min = -60.0; //StockBoundingBox.z_min;
    float z_max = 25.0; //StockBoundingBox.z_max;

    std::vector<std::vector<float>> sdf;

    float z_pos = z_max;
    while (z_pos >= z_min) {
        std::vector<float> column;
        float x_pos = x_min;
        while (x_pos <= x_max){
            Point point = {x_pos, z_pos};
            bool inside = isInside(point);
            float dist_clst_pnt = std::numeric_limits<float>::infinity(); 

            // find closest point on teh segment
            for (int i = 1; i < this->points.size(); i++) {

                //std::cout << "generate sdf" << i << "\n";
                Segment seg = {this->points[i-1], this->points[i]};
                Point clst = this->closest(point, seg.start, seg.end);
                
                //if (clst != NULL){
                    float clst_dist = this->distance_to(point, clst);
                    dist_clst_pnt = std::min(clst_dist, dist_clst_pnt);
                //}
            }

            float dist = abs(dist_clst_pnt);
            // print('dist', dist)
            if (inside){
                dist = -dist;
            }

            column.push_back(dist);
            x_pos += resolution;
        }

    sdf.push_back(column);
    // std::cout << "column " << column.size() << "\n";
    z_pos -= resolution;
    }

    //std::cout << "SDF::generate is Done" << std::endl;
    std::cout << "sdf" << sdf.size() << "\n";
    return sdf;
}

void SDF::add_point(float x, float z){
    this->points.push_back({x, z});
}

int SDF::point_count(){
    return this->points.size();
}

float SDF::distance_to(Point a, Point b){
    return sqrt((a.x- b.x) * (a.x- b.x) + (a.z - b.z) * (a.z - b.z));

}

Point SDF::closest(Point point, Point start, Point end){

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

int SDF::intersect(Segment a, Segment b){

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

bool SDF::isInside(Point point){
    int intersections = 0;

    // generate a ray to perform the crossing
    float x = point.x;
    float z = point.z + 100;
    Point plstart = {x, z};
    Segment projection_line = {plstart, point};
    
    for (int i = 1; i < this->points.size(); i++) {
        
        //std::cout << "Intersect point" << i << "\n";
        
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