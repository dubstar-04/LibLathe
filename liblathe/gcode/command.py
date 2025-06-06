class Command:
    def __init__(self, movement=None, params={}):
        self.movement = movement
        self.params = params

    def get_movement(self):
        """Returns the movement type for this command. (eg, GO, G1, G2, G3)"""

        return self.movement

    def getParams(self):
        """Returns the parameters for this command. (eg, X, Y ,Z, I, J, K and feed rate F)"""

        return self.params

    def to_string(self):
        """Returns this command as a string"""

        string = self.movement
        for param, value in self.params.items():
            string += " " + param + str(value)
        return string
