from decimal import Decimal
import math
from numbers import Real


def optimise_rapids(commands, tolerance=1e-6):
    """Return commands with redundant rapid moves removed.

    Rapids carry no feed word, stationary rapids are dropped, and consecutive
    collinear rapids are merged. A merged move stays within the original route,
    so previously certified clearance still applies.
    """

    result = []
    position = {}
    rapid_start = None
    for command in commands:
        movement = command.get_movement()
        params = command.getParams()
        if movement in ("G0", "G00"):
            params = {name: value for name, value in params.items() if name != "F"}
            target = {**position, **{name: params[name] for name in ("X", "Z") if name in params}}
            known = all(name in position for name in ("X", "Z")) and all(
                name in target for name in ("X", "Z"))
            if known and set(params) <= {"X", "Z"}:
                if (abs(target["X"] - position["X"]) <= tolerance
                        and abs(target["Z"] - position["Z"]) <= tolerance):
                    continue
                if rapid_start is not None:
                    first = (position["X"] - rapid_start[0], position["Z"] - rapid_start[1])
                    second = (target["X"] - position["X"], target["Z"] - position["Z"])
                    cross = first[0] * second[1] - first[1] * second[0]
                    if abs(cross) <= tolerance * max(1, math.hypot(*first) * math.hypot(*second)):
                        result.pop()
                        position = {"X": rapid_start[0], "Z": rapid_start[1]}
                        if (abs(target["X"] - position["X"]) <= tolerance
                                and abs(target["Z"] - position["Z"]) <= tolerance):
                            rapid_start = None
                            continue
                rapid_start = (position["X"], position["Z"])
            else:
                rapid_start = None
            result.append(Command(movement, params))
        else:
            rapid_start = None
            result.append(command)
        position.update({name: params[name] for name in ("X", "Z") if name in params})
    return result


class Command:
    def __init__(self, movement=None, params={}):
        self.movement = movement
        self.params = params

    def get_movement(self):
        """Returns the movement type for this command (for example G0, G1 or G33)."""

        return self.movement

    def getParams(self):
        """Returns axis, arc-offset, synchronization-lead and feed parameters."""

        return self.params

    def to_string(self):
        """Returns this command as a string"""

        string = self.movement
        for param, value in self.params.items():
            text = str(value)
            if isinstance(value, Real) and "e" in text.lower():
                # RS274 reads an exponent as another word, not part of this number.
                text = format(Decimal(text), "f")
            string += " " + param + text
        return string
