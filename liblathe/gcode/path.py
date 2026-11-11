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
                         return_to_clearance=False, contain_feeds=True):
        """Route rapids outside original stock and feed through approach/escape moves.

        Profile and roughing callers certify the added feeds against the part.
        Facing and parting may intentionally cut that region.
        Direction controls approach and retract moves, not the cutting segments.
        Auto prefers a cut-aligned entry and radial exit with axial fallback, and
        returns to the outside-stock corner between passes.
        Forced directions never fall back to another axis and reposition along
        their clearance plane, visiting the corner only at the start of the path.
        Local radial clearance uses prepared stock inside the selected Z range
        and actual stock elsewhere; all rapid transfers are certified.
        All feeds, including approach and withdrawal, stay inside tool-reference
        containment. Rapids must clear physical stock (or the model envelope
        when stock is not supplied). Missing boundary access is an error.
        """

        if not isinstance(direction, RoutingDirection):
            raise ValueError("Direction must be a RoutingDirection enumeration member")
        if radial_clearance is not None and (
                direction != RoutingDirection.RADIAL or not protect_part
                or not math.isfinite(radial_clearance) or operation.stock is None):
            raise ValueError("Local radial clearance requires protected radial routing and actual stock")
        if return_to_clearance and radial_clearance is None:
            raise ValueError("Returning to clearance requires local radial routing")
        if not contain_feeds:
            raise ValueError("Feed containment cannot be disabled")

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
            stock = operation.stock if operation.stock is not None else part_bounds
            radial_limit = stock.XMax
            if radial_clearance is not None:
                low = min(start.Z, end.Z) + tool_bounds.ZMin
                high = max(start.Z, end.Z) + tool_bounds.ZMax
                if low >= limits.ZMin - 1e-5 and high <= limits.ZMax + 1e-5:
                    stock = limits
                    radial_limit = limits.XMax + tool_bounds.XMin
            return (min(start.X, end.X) + tool_bounds.XMin >= radial_limit - 1e-5
                    or min(start.Z, end.Z) + tool_bounds.ZMin >= stock.ZMax - 1e-5
                    or max(start.Z, end.Z) + tool_bounds.ZMax <= stock.ZMin + 1e-5)

        def emit(movement, point):
            previous = commands[-1] if commands else self.commands[-1]
            params = previous.getParams()
            if 'X' in params and 'Z' in params:
                start = Point(params['X'], params['Z'])
                if movement == 'G1':
                    for endpoint in (point, start):
                        if not (limits.XMin - 1e-5 <= endpoint.X <= limits.XMax + 1e-5
                                and limits.ZMin - 1e-5 <= endpoint.Z <= limits.ZMax + 1e-5):
                            raise ValueError("Feed move is outside containment")
                elif movement == 'G0':
                    if not clears_stock(start, point):
                        raise ValueError("Rapid transfer crosses stock outside the prepared groove region"
                                         if radial_clearance is not None else
                                         "Rapid transfer crosses stock")
                    clear_feed(start, point)
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
            previous = commands[-1] if commands else self.commands[-1]
            position = Point(previous.getParams()['X'], previous.getParams()['Z'])
            entry_x = operation.containment.XMax if contain_feeds else x_clear
            entry_z = operation.containment.ZMax if contain_feeds else z_clear
            entries = (Point(target.X, entry_z), Point(entry_x, target.Z))
            if contain_feeds and segment.bulge == 0:
                aligned = boundary_point(target, target.X - segment.end.X,
                                         target.Z - segment.end.Z)
                entries = (aligned, *entries)
            if direction == RoutingDirection.RADIAL:
                entries = (Point(limits.XMax, target.Z),)
            elif direction == RoutingDirection.AXIAL:
                entries = (Point(target.X, limits.ZMax),)
            for entry in entries:
                try:
                    clear_feed(entry, target)
                except RuntimeError:
                    continue
                if contain_feeds:
                    corners = (Point(entry.X, position.Z), Point(position.X, entry.Z))
                    if direction == RoutingDirection.RADIAL:
                        corners = tuple(reversed(corners))
                    for corner in corners:
                        if not (clears_stock(position, corner) and clears_stock(corner, entry)):
                            continue
                        try:
                            clear_feed(position, corner)
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
            raise ValueError("Cannot approach within containment from stock clearance. "
                             "Enlarge containment to include a stock-clear feed entry.")

        def retract(segment):
            origin = segment.end
            exit_x = operation.containment.XMax if contain_feeds else x_clear
            exit_z = operation.containment.ZMax if contain_feeds else z_clear
            exits = (Point(exit_x, origin.Z), Point(origin.X, exit_z))
            if direction == RoutingDirection.RADIAL:
                exits = (Point(limits.XMax, origin.Z),)
            elif direction == RoutingDirection.AXIAL:
                exits = (Point(origin.X, limits.ZMax),)
            for exit_point in exits:
                if direction == RoutingDirection.AUTO and segment.bulge == 0:
                    dx, dz = origin.X - segment.start.X, origin.Z - segment.start.Z
                    ex, ez = exit_point.X - origin.X, exit_point.Z - origin.Z
                    if (dx * ex + dz * ez < 0
                            and abs(dx * ez - dz * ex) <= 1e-6 * max(
                                1, math.hypot(dx, dz) * math.hypot(ex, ez))):
                        continue
                destination = (outside if direction == RoutingDirection.AUTO else
                               Point(x_clear, origin.Z) if direction == RoutingDirection.RADIAL else
                               Point(origin.X, z_clear))
                corners = (Point(destination.X, exit_point.Z), Point(exit_point.X, destination.Z))
                route = None
                try:
                    clear_feed(origin, exit_point)
                    for corner in corners:
                        if not (clears_stock(exit_point, corner) and clears_stock(corner, destination)):
                            continue
                        try:
                            clear_feed(exit_point, corner)
                            clear_feed(corner, destination)
                        except RuntimeError:
                            continue
                        route = (corner, destination)
                        break
                except RuntimeError:
                    continue
                if route is None:
                    continue
                emit('G1', exit_point)
                for point in route:
                    if point.isSame(exit_point):
                        continue
                    emit('G0', point)
                    exit_point = point
                return
            raise ValueError("Cannot retract within containment to stock clearance. "
                             "Enlarge containment to include a stock-clear feed withdrawal.")

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
