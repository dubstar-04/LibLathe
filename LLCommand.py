class Command:
    def __init__(self, Movement=None, Params={}):
        self.Movement = Movement
        self.Params = Params

    def get_movement(self):
        '''
        Returns the movement type for this command. (eg, GO, G1, G2, G3)
        '''
        return self.Movement

    def get_params(self):
        '''
        Returns the parameters for this command. (eg, X, Y ,Z, I, J, K and feed rate F)
        '''
        return self.Params

    def to_string(self):
        '''
        Returns this command as a string
        '''
        string = self.Movement
        for param, value in self.Params.items():
            string += " " + param + str(value)
        return string
