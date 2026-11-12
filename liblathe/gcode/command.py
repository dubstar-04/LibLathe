from decimal import Decimal
from numbers import Real


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
