#include "segmentgroup.h"
       
    SegmentGroup::SegmentGroup()
    {
        
    }

    void SegmentGroup::add_segment(Segment segment){
        //Add segment to group //
        this->segments.push_back(segment);
    }

    void SegmentGroup::insert_segment(Segment segment, int position){
        //Insert segment into group at position //
        segments.insert(segments.begin() + position, segment);
    }

    std::vector<Segment> SegmentGroup::get_segments(){
        //Return segments of group as a list //
        return this->segments;
    }
    
    void SegmentGroup::extend(SegmentGroup segmentgroup){
        //Add segment group to this segmentgroup //
        std::vector<Segment> segs = segmentgroup.get_segments();
        this->segments.insert(segments.end(), segs.begin(), segs.end());
    }

    int SegmentGroup::count(){
        //Return the number of segments in the segmentgroup //
        return this->segments.size();
    }

    BoundBox SegmentGroup::boundbox(){
        //Return the boundbox for the segmentgroup//
        
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
        return *this;
    }
 

    SegmentGroup SegmentGroup::defeature(BoundBox stock, int tool, bool allow_grooving=false){
        // Defeature the segment group. Remove features that cannot be turned. e.g. undercuts / grooves //

        //tool temp assigned as an int
        return *this;
    }

    void SegmentGroup::validate(){
        //validate the segment group//
    }

