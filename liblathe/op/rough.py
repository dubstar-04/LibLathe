from collections import namedtuple

import liblathe.op.base
from liblathe.base.point import Point
from liblathe.base.boundbox import BoundBox
from liblathe.base.segment import Segment
from liblathe.base.segmentgroup import SegmentGroup

# create a namedtuple to hold intersection data
Intersection = namedtuple('Intersection', 'point, seg')


class RoughOP(liblathe.op.base.BaseOP):

    def generatePath(self):
        """Replace toolpaths on success; leave no published paths on failure."""
        self.tool_paths = []
        tool_paths = []
        roughing_segmentGroup = self._defeature_profile(self.allow_grooving)

        # internal segment group to check if intersects the part. use a small offset to reduce false positives
        internalOffset = roughing_segmentGroup.offset(-0.1)

        ZMax = self.containment.ZMax
        ZMin = self.containment.ZMin

        # create roughing boundary offset by the stock to leave value
        # include a minimal offset to ensure the roughing passes don't intersect the part
        offset = 0.01 + self.stock_to_leave
        roughing_boundary = roughing_segmentGroup.offset(offset, extend_start=True)

        # define the x limits for roughing
        XMin = self.containment.XMin
        XMax = self.containment.XMax
        limits = BoundBox(Point(XMin, ZMin), Point(XMax, ZMax))

        # Offset sampling can stop short of the inner radius. Cap its front
        # endpoint so the innermost pass still has a trimming intersection.
        boundary_segments = roughing_boundary.getSegments()
        if boundary_segments and boundary_segments[0].start.X > XMin:
            front = boundary_segments[0].start
            boundary = SegmentGroup()
            boundary.addSegment(Segment(Point(XMin, front.Z), front))
            boundary.extend(roughing_boundary)
            roughing_boundary = boundary

        x_pos = XMin
        # Generate passes from the inner limit outward; G-code traverses them in reverse.
        while x_pos < XMax:
            pt1 = Point(x_pos, ZMax)
            pt2 = Point(x_pos, ZMin)
            path_line = Segment(pt1, pt2)
            intersections = []
            for seg in roughing_boundary.getSegments():
                points = seg.intersect(path_line)
                if len(points):
                    for p in points:
                        intersection = Intersection(p, seg)
                        intersections.append(intersection)

            # build list of segments
            segmentgroup = SegmentGroup()

            if not intersections:
                seg = path_line
                # add passes with no intersections only if they're outside the part radius
                if x_pos >= roughing_boundary.boundbox().XMax:
                    segmentgroup.addSegment(seg)

            if len(intersections) == 1:
                # Only one intersection, trim line to intersection.
                seg = Segment(pt1, intersections[0].point)
                segmentgroup.addSegment(seg)
                if intersections[0].seg:
                    # add lead out
                    self._add_lead(segmentgroup, intersections[0].point,
                                   self.leadout_angle, limits)

            if len(intersections) > 1:
                # more than one intersection
                # add the end points of the pass to generate new segments
                if not roughing_boundary.isInside(pt1):
                    intersection = Intersection(pt1, None)
                    intersections.insert(0, intersection)

                if not roughing_boundary.isInside(pt2):
                    intersection2 = Intersection(pt2, None)
                    intersections.append(intersection2)

                #  sort the a list of intersections by their z position
                intersections = sorted(intersections, key=lambda p: p.point.Z, reverse=True)

                for i in range(len(intersections)):
                    if i + 1 < len(intersections):
                        if i % 2 == 0:
                            # primary segment
                            primary_segment = Segment(intersections[i].point, intersections[i + 1].point)

                            # check the length of the pass before adding to the segmentgroup
                            if primary_segment.getLength() < self.pass_offset:
                                continue

                            # if the intersection is connected to another segment
                            if intersections[i].seg:
                                # add a lead in
                                self._add_lead(segmentgroup, intersections[i].point,
                                               self.leadin_angle, limits, lead_in=True)

                            # add the primary segment to the segment group
                            segmentgroup.addSegment(primary_segment)

                            # if the intersection is connected to another segment
                            if intersections[i + 1].seg:
                                # add a lead out
                                self._add_lead(segmentgroup, intersections[i + 1].point,
                                               self.leadout_angle, limits)

            x_pos += self.pass_offset

            if segmentgroup.count():
                if segmentgroup.intersectsGroup(internalOffset):
                    # Debug().draw([segmentgroup, self.partSegmentGroup, roughing_boundary])
                    raise ValueError("Calculated roughing path intersects part")

                for segment in segmentgroup.getSegments():
                    self.partSegmentGroup.validateToolSweep(
                        self.tool.get_segmentgroup(), segment.start, segment.end)
                tool_paths.append(segmentgroup)

        self.tool_paths = tool_paths
