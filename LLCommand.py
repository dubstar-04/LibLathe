class Command:
    def __init__(self, Movement = None, Params = {}):
        self.Movement = Movement
        self.Params = Params
        
    def get_movement(self):
        return self.Movement

    def get_params(self):
        return self.Params
