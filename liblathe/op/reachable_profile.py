from bisect import bisect_left, bisect_right
import math

from liblathe.base.point import Point
from liblathe.base.segmentgroup import SegmentGroup


_PROFILE_EPSILON = 1e-6
_SAMPLED_WALL_THRESHOLD = SegmentGroup.offsetTolerance


class ReachableProfile:
    """A strictly ordered sampled radial limit X(Z)."""

    def __init__(self, samples, *, _conservative=True):
        source_samples = tuple(samples)
        if len(source_samples) < 2:
            raise ValueError("A reachable profile requires at least two samples")
        if any(not math.isfinite(point.X) or not math.isfinite(point.Z)
               for point in source_samples):
            raise ValueError("Profile samples must be finite")
        if any(first.Z <= second.Z for first, second in zip(source_samples, source_samples[1:])):
            raise ValueError("Profile samples must be strictly ordered from high Z to low Z")
        radial_values = [point.X for point in source_samples]
        if _conservative:
            for index, (first, second) in enumerate(zip(source_samples, source_samples[1:])):
                if abs(first.X - second.X) > _SAMPLED_WALL_THRESHOLD:
                    outer_radius = max(first.X, second.X)
                    radial_values[index] = max(radial_values[index], outer_radius)
                    radial_values[index + 1] = max(radial_values[index + 1], outer_radius)
        self.samples = tuple(
            Point(radial, point.Z) for radial, point in zip(radial_values, source_samples)
        )
        self._ascending = tuple(reversed(self.samples))
        self._ascending_z = tuple(point.Z for point in self._ascending)

    def offset(self, distance):
        """Dilate the sampled profile by a circular stock allowance."""
        distance = float(distance)
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Profile offset must be finite and non-negative")

        target_zs = [point.Z for point in self.samples]
        if distance:
            extension_steps = max(
                1, math.ceil(math.sqrt(distance / (2 * SegmentGroup.defeatureResolution)))
            )
            step = distance / extension_steps
            for index in range(1, extension_steps + 1):
                target_zs.append(self.samples[0].Z + step * index)
                target_zs.append(self.samples[-1].Z - step * index)
        target_zs = sorted(set(target_zs), reverse=True)

        offset = []
        for target_z in target_zs:
            first = max(0, bisect_left(self._ascending_z, target_z - distance) - 1)
            last = min(len(self._ascending) - 2,
                       bisect_right(self._ascending_z, target_z + distance) - 1)
            maximum_x = -math.inf
            for index in range(first, last + 1):
                start, end = self._ascending[index:index + 2]
                slope = (end.X - start.X) / (end.Z - start.Z)
                optimum_z = target_z + slope * distance / math.hypot(1, slope)
                lower_z = max(start.Z, target_z - distance)
                upper_z = min(end.Z, target_z + distance)
                if lower_z > upper_z:
                    continue
                source_z = min(upper_z, max(lower_z, optimum_z))
                axial_delta = target_z - source_z
                source_x = start.X + slope * (source_z - start.Z)
                candidate_x = source_x + math.sqrt(
                    max(0, distance * distance - axial_delta * axial_delta)
                )
                maximum_x = max(maximum_x, candidate_x)
            if not math.isfinite(maximum_x):
                raise ValueError("Profile offset could not be calculated")
            offset.append(Point(maximum_x, target_z))
        return ReachableProfile(offset, _conservative=False)

    def intervals_below(self, radial_limit):
        """Return high-Z/low-Z intervals at or inside a radial limit."""
        radial_limit = float(radial_limit)
        if not math.isfinite(radial_limit):
            raise ValueError("Radial limit must be finite")

        intervals = []
        active = self.samples[0].X <= radial_limit + _PROFILE_EPSILON
        start_z = self.samples[0].Z if active else None
        for first, second in zip(self.samples, self.samples[1:]):
            next_active = second.X <= radial_limit + _PROFILE_EPSILON
            if active != next_active:
                denominator = second.X - first.X
                fraction = 0 if denominator == 0 else (radial_limit - first.X) / denominator
                crossing_z = first.Z + min(1, max(0, fraction)) * (second.Z - first.Z)
                if active:
                    if start_z - crossing_z > _PROFILE_EPSILON:
                        intervals.append((start_z, crossing_z))
                    start_z = None
                else:
                    start_z = crossing_z
            active = next_active
        if active and start_z - self.samples[-1].Z > _PROFILE_EPSILON:
            intervals.append((start_z, self.samples[-1].Z))
        return intervals

    def intervals_between(self, lower_limit, upper_limit):
        """Return high-Z/low-Z intervals within a half-open radial band."""
        lower_limit, upper_limit = float(lower_limit), float(upper_limit)
        if not math.isfinite(lower_limit) or not math.isfinite(upper_limit):
            raise ValueError("Radial limits must be finite")
        if lower_limit >= upper_limit:
            raise ValueError("Lower radial limit must be less than upper radial limit")

        included = self.intervals_below(upper_limit)
        excluded = self.intervals_below(lower_limit)
        intervals = []
        excluded_index = 0
        for high, low in included:
            while (excluded_index < len(excluded)
                   and excluded[excluded_index][0] > high + _PROFILE_EPSILON):
                excluded_index += 1
            cursor = high
            while (excluded_index < len(excluded)
                   and excluded[excluded_index][0] > low + _PROFILE_EPSILON):
                excluded_high, excluded_low = excluded[excluded_index]
                if cursor - excluded_high > _PROFILE_EPSILON:
                    intervals.append((cursor, excluded_high))
                cursor = min(cursor, excluded_low)
                excluded_index += 1
            if cursor - low > _PROFILE_EPSILON:
                intervals.append((cursor, low))
        return intervals

    def value_at(self, axial_position):
        """Interpolate the radial limit at an in-range axial position."""
        axial_position = float(axial_position)
        if not math.isfinite(axial_position):
            raise ValueError("Axial position must be finite")
        if axial_position > self.samples[0].Z or axial_position < self.samples[-1].Z:
            raise ValueError("Axial position is outside the reachable profile")

        index = bisect_left(self._ascending_z, axial_position)
        if (index < len(self._ascending)
                and self._ascending[index].Z == axial_position):
            return self._ascending[index].X
        low = self._ascending[index - 1]
        high = self._ascending[index]
        fraction = (axial_position - low.Z) / (high.Z - low.Z)
        return low.X + fraction * (high.X - low.X)
