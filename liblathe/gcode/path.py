import math
from enum import Enum

from liblathe.gcode.command import Command
from liblathe.base.point import Point
from liblathe.base.segment import Segment


class RoutingDirection(Enum):
    AUTO = "Auto"
    RADIAL = "Radial"
    AXIAL = "Axial"


class Path:
    """Container Group for gcode path commands"""

    def __init__(self):
        self.commands = []

        cmd = Command('G18')  # xz plane
        self.commands.append(cmd)

    def get_min_retract_x(self, segment, pass_segments, operation):
        """ returns the minimum x retract based on the current segments and the partSegments """

        # partSegments = partSegmentGroup.getSegments()
        currentIdx = pass_segments.index(segment)
        x_values = []

        # get the XMax from the current pass segments
        for idx, seg in enumerate(pass_segments):
            x_values.extend([seg.Boundbox().XMin, seg.Boundbox().XMax])
            if idx == currentIdx:
                break

        # get the XMax from the part segments up to the z position of the current segment
        seg_ZMax = segment.Boundbox().ZMax
        for part_seg in operation.partSegmentGroup.getSegments():

            part_seg_ZMax = part_seg.Boundbox().ZMax
            x_values.extend([part_seg.Boundbox().XMin, part_seg.Boundbox().XMax])

            if part_seg_ZMax < seg_ZMax:
                break

        min_retract_x = max(x_values, key=abs)
        return min_retract_x

    def previous_segment_connected(self, segments, segment):
        """returns bool if segment is connect to the previous segment"""

        currentIdx = segments.index(segment)
        previousIdx = currentIdx - 1

        if not currentIdx == 0:
            currentStartPt = segment.start
            previousEndPt = segments[previousIdx].end

            if currentStartPt.isSame(previousEndPt):
                return True

        return False

    def fromSegmentGroup(self, operation, segmentGroup, *, protect_part=False,
                         direction=RoutingDirection.AUTO, radial_clearance=None,
                         return_to_clearance=False, contain_feeds=False):
        """Route rapids outside original stock and feed through approach/escape moves.

        Profile and roughing callers certify the added feeds against the part.
        Facing and parting may intentionally cut that region.
        Direction controls approach and retract moves, not the cutting segments.
        Auto retains axial-first entry and radial-first exit with fallback, and
        returns to the outside-stock corner between passes.
        Forced directions never fall back to another axis and reposition along
        their clearance plane, visiting the corner only at the start of the path.
        Local radial clearance uses prepared stock inside the selected Z range
        and actual stock elsewhere; all rapid transfers are certified.
        With contain_feeds, cutting and entry feeds stay inside tool-reference
        containment. Radial feed withdrawals may leave it to reach stock clearance;
        rapid transfers must clear the physical stock.
        """

        if not isinstance(direction, RoutingDirection):
            raise ValueError("Direction must be a RoutingDirection enumeration member")
        if radial_clearance is not None and (
                direction != RoutingDirection.RADIAL or not protect_part
                or not math.isfinite(radial_clearance) or operation.stock is None):
            raise ValueError("Local radial clearance requires protected radial routing and actual stock")
        if return_to_clearance and radial_clearance is None:
            raise ValueError("Returning to clearance requires local radial routing")
        if contain_feeds and (direction != RoutingDirection.AUTO or radial_clearance is not None
                              or not protect_part):
            raise ValueError("Contained feeds require protected automatic routing")

        def get_pos(pnt):
            x = pnt.X
            z = pnt.Z

            return Point(x, z)

        def get_arc_type(bulge):
            if bulge > 0:
                arcType = 'G3'
            else:
                arcType = 'G2'

            return arcType

        segments = segmentGroup.getSegments()
        if not segments:
            return
        clearance = float(operation.clearance)
        if not math.isfinite(clearance) or clearance < 0:
            raise ValueError("Clearance must be finite and non-negative")
        clearance = max(clearance, 0.01)
        tool = operation.tool.get_segmentgroup()
        tool_bounds = tool.boundbox()
        part_bounds = operation.partSegmentGroup.boundbox()
        pass_bounds = segmentGroup.boundbox()
        if contain_feeds:
            limits = operation.containment
            if not (pass_bounds.XMin >= limits.XMin - 1e-5
                    and pass_bounds.XMax <= limits.XMax + 1e-5
                    and pass_bounds.ZMin >= limits.ZMin - 1e-5
                    and pass_bounds.ZMax <= limits.ZMax + 1e-5):
                raise ValueError("Cutting path is outside containment")
        x_clear = max(operation.containment.XMax - tool_bounds.XMin,
                      part_bounds.XMax - tool_bounds.XMin, pass_bounds.XMax) + clearance
        z_clear = max(operation.containment.ZMax - tool_bounds.ZMin,
                      part_bounds.ZMax - tool_bounds.ZMin, pass_bounds.ZMax) + clearance
        if radial_clearance is not None or (contain_feeds and operation.stock is not None):
            actual = operation.stock
            x_clear = max(x_clear, actual.XMax - tool_bounds.XMin + clearance)
            z_clear = max(z_clear, actual.ZMax - tool_bounds.ZMin + clearance)
        if not all(math.isfinite(value) for value in (x_clear, z_clear)):
            raise ValueError("Containment, stock and tool clearance coordinates must be finite")
        outside = Point(x_clear, z_clear)
        if radial_clearance is not None:
            if radial_clearance < operation.containment.XMax - tool_bounds.XMin + clearance:
                raise ValueError("Local radial clearance is inside the prepared stock clearance")
            x_clear = radial_clearance
        commands = []

        def clears_stock(start, end):
            stock = operation.stock if operation.stock is not None else operation.containment
            return (min(start.X, end.X) + tool_bounds.XMin >= stock.XMax - 1e-5
                    or min(start.Z, end.Z) + tool_bounds.ZMin >= stock.ZMax - 1e-5
                    or max(start.Z, end.Z) + tool_bounds.ZMax <= stock.ZMin + 1e-5)

        def emit(movement, point, *, withdrawal=False):
            if contain_feeds:
                previous = commands[-1] if commands else self.commands[-1]
                params = previous.getParams()
                if movement == 'G1' and not withdrawal:
                    limits = operation.containment
                    for endpoint in (point, Point(params['X'], params['Z'])):
                        if not (limits.XMin - 1e-5 <= endpoint.X <= limits.XMax + 1e-5
                                and limits.ZMin - 1e-5 <= endpoint.Z <= limits.ZMax + 1e-5):
                            raise ValueError("Feed move is outside roughing containment")
                elif movement == 'G0' and 'X' in params and 'Z' in params:
                    start = Point(params['X'], params['Z'])
                    if not clears_stock(start, point):
                        raise ValueError("Rapid transfer crosses stock")
                    operation.partSegmentGroup.validateToolSweep(tool, start, point)
            if movement == 'G0' and radial_clearance is not None:
                previous = commands[-1] if commands else self.commands[-1]
                params = previous.getParams()
                if 'X' in params and 'Z' in params:
                    start = Point(params['X'], params['Z'])
                    low = min(start.Z, point.Z) + tool_bounds.ZMin
                    high = max(start.Z, point.Z) + tool_bounds.ZMax
                    prepared = (low >= operation.containment.ZMin - 1e-5
                                and high <= operation.containment.ZMax + 1e-5)
                    envelope = operation.containment if prepared else operation.stock
                    if not (min(start.X, point.X) + tool_bounds.XMin > envelope.XMax
                            or low > envelope.ZMax or high < envelope.ZMin):
                        raise ValueError("Rapid transfer crosses stock outside the prepared groove region")
                    operation.partSegmentGroup.validateToolSweep(tool, start, point)
            commands.append(Command(movement, {'X': point.X, 'Z': point.Z, 'F': operation.hfeed}))

        def clear_feed(start, end):
            if protect_part:
                operation.partSegmentGroup.validateToolSweep(tool, start, end)

        def boundary_point(anchor, dx, dz):
            limits = operation.containment
            distances = []
            for value, delta, low, high in (
                    (anchor.X, dx, limits.XMin, limits.XMax),
                    (anchor.Z, dz, limits.ZMin, limits.ZMax)):
                if delta > 0:
                    distances.append((high - value) / delta)
                elif delta < 0:
                    distances.append((low - value) / delta)
            distance = max(0, min(distances)) if distances else 0
            return Point(anchor.X + distance * dx, anchor.Z + distance * dz)

        def approach(segment):
            target = segment.start
            if radial_clearance is not None:
                previous = commands[-1] if commands else self.commands[-1]
                if abs(previous.getParams()['X'] - x_clear) > 1e-6:
                    emit('G0', Point(outside.X, target.Z))
            entry_x = operation.containment.XMax if contain_feeds else x_clear
            entry_z = operation.containment.ZMax if contain_feeds else z_clear
            entries = (Point(target.X, entry_z), Point(entry_x, target.Z))
            if contain_feeds and segment.bulge == 0:
                aligned = boundary_point(target, target.X - segment.end.X,
                                         target.Z - segment.end.Z)
                entries = (aligned, *entries)
            if direction == RoutingDirection.RADIAL:
                entries = (Point(x_clear, target.Z),)
            elif direction == RoutingDirection.AXIAL:
                entries = (Point(target.X, z_clear),)
            for entry in entries:
                try:
                    clear_feed(entry, target)
                except RuntimeError:
                    continue
                if contain_feeds:
                    for corner in (Point(entry.X, outside.Z), Point(outside.X, entry.Z)):
                        if not (clears_stock(outside, corner) and clears_stock(corner, entry)):
                            continue
                        try:
                            clear_feed(outside, corner)
                            clear_feed(corner, entry)
                        except RuntimeError:
                            continue
                        break
                    else:
                        continue
                    emit('G0', corner)
                emit('G0', entry)
                emit('G1', target)
                return
            raise ValueError("Cannot approach the pass safely; extend containment beyond stock"
                             if contain_feeds else
                             "Cannot approach the pass without crossing the protected part")

        def retract(segment):
            origin = segment.end
            exit_x = operation.containment.XMax if contain_feeds else x_clear
            exit_z = operation.containment.ZMax if contain_feeds else z_clear
            exits = (Point(exit_x, origin.Z), Point(origin.X, exit_z))
            if contain_feeds:
                exits = (Point(x_clear, origin.Z),)
            if direction == RoutingDirection.RADIAL:
                exits = (Point(x_clear, origin.Z),)
            elif direction == RoutingDirection.AXIAL:
                exits = (Point(origin.X, z_clear),)
            for exit_point in exits:
                if contain_feeds and segment.bulge == 0:
                    dx, dz = origin.X - segment.start.X, origin.Z - segment.start.Z
                    ex, ez = exit_point.X - origin.X, exit_point.Z - origin.Z
                    if (dx * ex + dz * ez < 0
                            and abs(dx * ez - dz * ex) <= 1e-6 * max(
                                1, math.hypot(dx, dz) * math.hypot(ex, ez))):
                        continue
                if contain_feeds and not clears_stock(exit_point, outside):
                    continue
                try:
                    clear_feed(origin, exit_point)
                    if contain_feeds:
                        clear_feed(exit_point, outside)
                except RuntimeError:
                    continue
                emit('G1', exit_point, withdrawal=contain_feeds)
                if direction == RoutingDirection.AUTO:
                    emit('G0', outside)
                return
            raise ValueError("Cannot withdraw radially to stock clearance without crossing "
                             "the protected part or reversing the cut"
                             if contain_feeds else
                             "Cannot retract the insert without crossing the protected part")

        # forced directions stay on their clearance plane, so the corner is only needed to enter the path
        if direction == RoutingDirection.AUTO or len(self.commands) == 1:
            emit('G0', outside)
        for index, seg in enumerate(segments):
            if index == 0 or not self.previous_segment_connected(segments, seg):
                if index:
                    retract(segments[index - 1])
                approach(seg)

            if seg.bulge == 0:
                pt = get_pos(seg.end)
                params = {'X': pt.X, 'Z': pt.Z, 'F': operation.hfeed}
                cmd = Command('G1', params)
                commands.append(cmd)
            # handle arc segments
            if seg.bulge != 0:
                pt1 = get_pos(seg.start)
                pt2 = get_pos(seg.end)
                # set the arc direction
                arcType = get_arc_type(seg.bulge)

                # set the arc parameters
                cen = get_pos(seg.getCentrePoint()).sub(pt1)
                params = {'X': pt2.X, 'Z': pt2.Z, 'I': cen.X, 'K': cen.Z, 'F': operation.hfeed}
                cmd = Command(arcType, params)
                commands.append(cmd)

        retract(segments[-1])
        if return_to_clearance:
            emit('G0', Point(outside.X, segments[-1].end.Z))
            emit('G0', outside)
        self.commands.extend(commands)
