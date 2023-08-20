#include <algorithm>

#include "boundbox.h"
#include "point.h"
#include "utils.h"
#include "segment.h"

#ifndef SegmentGroup_H
#define SegmentGroup_H

class SegmentGroup
{
    public:
        SegmentGroup();
        ~SegmentGroup(){};

        void add_segment(Segment segment);
        void insert_segment(Segment segment, int position);
        std::vector<Segment> get_segments();
        void extend(SegmentGroup segmentgroup);
        int count();
        BoundBox boundbox();
        bool intersects_group(SegmentGroup segment_group);
        SegmentGroup offset(float step_over);
        SegmentGroup defeature(BoundBox stock, int tool, bool allow_grooving);
        void validate();

    private:
    std::vector<Segment> segments;

};

#endif
