#include <iostream>

#include "segmentgroup.h"
       
    SegmentGroup::SegmentGroup()
    {
        
    }

    void SegmentGroup::add_segment(Segment segment){
        // Add segment to group //
        this->segments.push_back(segment);
    }

    void SegmentGroup::insert_segment(Segment segment, int position){
        // Insert segment into group at position //
        segments.insert(segments.begin() + position, segment);
    }

    std::vector<Segment> SegmentGroup::get_segments(){
        // Return segments //
        return this->segments;
    }
    
    void SegmentGroup::extend(SegmentGroup segmentgroup){
        // Add segment group to this segmentgroup //
        std::vector<Segment> segs = segmentgroup.get_segments();
        this->segments.insert(segments.end(), segs.begin(), segs.end());
    }

    int SegmentGroup::count(){
        // Return the number of segments in the segmentgroup //
        return this->segments.size();
    }

    BoundBox SegmentGroup::boundbox(){
        // Return the boundbox for the segmentgroup //

        if(this->count() == 0){
            return BoundBox(Point(), Point());
        }
        
        std::vector<float> xvalues;
        std::vector<float> zvalues;

        // collect all points from each segment by direction
        for (auto &segment : this->segments)
        {
            BoundBox bb = segment.get_boundbox();

            xvalues.push_back(bb.x_min);
            xvalues.push_back(bb.x_max);

            zvalues.push_back(bb.z_min);
            zvalues.push_back(bb.z_max);
        }

        float x_min = *std::min_element(std::begin(xvalues), std::end(xvalues));
        float x_max = *std::max_element(std::begin(xvalues), std::end(xvalues));
        float z_min = *std::min_element(zvalues.begin(), zvalues.end());
        float z_max = *std::max_element(zvalues.begin(), zvalues.end());

        Point pt1 = Point(x_min, z_min);
        Point pt2 = Point(x_max, z_max);
        BoundBox segmentgroupBoundBox = BoundBox(pt1, pt2);

        return segmentgroupBoundBox;
    }
    
    bool SegmentGroup::intersects_group(SegmentGroup segment_group){
        // check if the segment_group intersects self //
        for (auto &segment : segment_group.get_segments()){
            for(auto &seg : this->segments){
                //TODO: remove false from intersect call
                std::vector<Point> points = segment.intersect(seg, false);
                if(points.size() > 0){
                    return true;
                }
            }
        }

        return false;
    }

    SegmentGroup SegmentGroup::offset(float step_over){
        // Create an offset segmentgroup by the distance of step_over //

        BoundBox bb = this->boundbox();
        float height = bb.x_length() + 10;
        float width = bb.z_length() + 10;

        Point center = Point( height / 2, bb.z_min + width / 2);

        //std::cout << "quadtree: " << width << " " << height << " " << center.x << " " << center.z << std::endl;
        Quadtree qt = Quadtree();
        //qt.add_segments(this->segments);
        qt.initialise(this, center, width, height);
        //qt.add_base_node(center, width, height);
        std::vector<Point> offset = qt.get_offset(step_over);

        // attempt simplification
        float resolution = 0.01;
        std::vector<Point> defeatured_points;
        this->rdp(offset, resolution, defeatured_points);
        return this->from_points(defeatured_points);

    }
 

    SegmentGroup SegmentGroup::defeature(BoundBox stock, SegmentGroup tool, bool allow_grooving=false){
        // Defeature the segment group. Remove features that cannot be turned. e.g. undercuts / grooves etc //

        float x_min = 0;
        float x_max = stock.x_max;
        float z_min = stock.z_min;
        float z_max = stock.z_max;
        float resolution = 0.01;

        std::vector<Point> points;

        float z_pos = z_max;
        while (z_pos > z_min){

            
            // test for intersection at z with a single segment
            Segment test_segment = Segment(Point(x_max, z_pos), Point(x_min, z_pos));

            for(auto seg : this->segments){
                //TODO: remove the bool false from the segment call
                std::vector<Point> pts = test_segment.intersect(seg, false);
                if (pts.size() > 0){
                    float x_pos = pts[0].x - resolution;
                    // std::cout << " defeature " << x_pos << " " << z_pos << std::endl;
                    while (x_pos < (pts[0].x + resolution)){
                        Point iteration_position = Point(x_pos, z_pos);
                        SegmentGroup tool_shape = tool.add(iteration_position); // = tool.get_shape_group(iteration_position);
                        if (!intersects_group(tool_shape)){
                            
                            // if allow_grooving is false
                            if (points.size() > 1 && allow_grooving == false){
                                float last_x = points.back().x;
                                if (x_pos < last_x){
                                    iteration_position.x = last_x;
                                }
                            }

                            points.push_back(iteration_position);
                            break;
                        }
                        x_pos += resolution * 0.5;
                    }
                    break;
                }
            }

            z_pos -= resolution;
        }

        // attempt simplification
        std::vector<Point> defeatured_points;
        this->rdp(points, resolution, defeatured_points);
        return this->from_points(defeatured_points);
    }

SegmentGroup SegmentGroup::add(Point point){
    // add point to each segment of the segment group //

    SegmentGroup out;

    for(auto seg : this->segments){

        Point start = Point(seg.start.x + point.x, seg.start.z + point.z);
        Point end = Point(seg.end.x + point.x, seg.end.z + point.z);
        Segment new_seg = Segment(start, end);
        out.add_segment(new_seg);
    }

    return out;
}

SegmentGroup SegmentGroup::from_points(std::vector<Point> points){
    // create a segment group from a vector of points //
    SegmentGroup segment_group = SegmentGroup();

    if (points.size() > 0){
        for(int i = 0; i < points.size(); i++){
            if(i >= 1){
                Segment seg = Segment(points[i-1], points[i]);
                segment_group.add_segment(seg);
            }
        }
    }

    return segment_group;
}

std::vector<Point> SegmentGroup::get_rdp(std::vector<Point> &points, float tolerance){
    std::vector<Point> out;
    this->rdp(points, tolerance, out);
    return out;
}

void SegmentGroup::rdp(std::vector<Point> &points, float tolerance, std::vector<Point> &out){

	if(points.size()<2){
        throw std::runtime_error("SegmentGroup error not enough points to simplify group");
    }

	// Find the point with the maximum distance from line between start and end
	double dmax = 0.0;
	size_t index = 0;
	size_t end = points.size()-1;
	for(size_t i = 1; i < end; i++)
	{
		double d = Segment(points[0], points[end]).distance_to_point(points[i]); //PerpendicularDistance(points[i], points[0], points[end]);
		if (d > dmax)
		{
			index = i;
			dmax = d;
		}
	}

	// If max distance is greater than tolerance, recursively simplify
	if(dmax > tolerance)
	{
		// Recursive call
		std::vector<Point> recResults1;
		std::vector<Point> recResults2;
		std::vector<Point> firstLine(points.begin(), points.begin() + index + 1);
		std::vector<Point> lastLine(points.begin() + index, points.end());
		this->rdp(firstLine, tolerance, recResults1);
		this->rdp(lastLine, tolerance, recResults2);
 
		// Build the result list
		out.assign(recResults1.begin(), recResults1.end()-1);
		out.insert(out.end(), recResults2.begin(), recResults2.end());
		if(out.size()<2){
		throw std::runtime_error("SegmentGroup error when performing point reduction");
        }
	} else {
		//Just return start and end points
		out.clear();
		out.push_back(points[0]);
		out.push_back(points[end]);
	}
}

    void SegmentGroup::validate(){
        //validate the segment group//

        // check each segment is connected

        // check that the group is open i.e, the start and end points are not connected

        // check that the start and end points are at x = 0 (only valid for the primary group / part shape)
    }


float SegmentGroup::sdv(Point point)
{   
    // return a signed distance value to the closest point on the segments //
    float sdv;

    bool inside = this->isInside(point);
    float dist_clst_pnt = std::numeric_limits<float>::infinity(); 

    // find closest point on the segments
   for(auto &segment : this->segments){
    float clst_dist = segment.distance_to_point(point);
    dist_clst_pnt = std::min(clst_dist, dist_clst_pnt);
   }

    sdv = abs(dist_clst_pnt);
    if (inside){
        sdv = -sdv;
    }

    return sdv;
}

bool SegmentGroup::isInside(Point point){
    // determin in point is inside the segments //
    int intersections = 0;

    // generate a ray to perform the crossing
    float x = point.x;
    // ensure that the ray starts outside the segments boundbox
    float z = this->boundbox().z_max + 10;
    Segment ray = Segment(Point(x, z), point);
    
    // collect the number of times ray intersects the segments
   for( auto &segment : this->segments){
        std::vector<Point> pnts = ray.intersect(segment, false);
        intersections += pnts.size();
   }

    if (intersections % 2 == 0 && intersections > 0 || intersections == 0){
        //even
        return false;
    }
    //odd
    return true;
}

