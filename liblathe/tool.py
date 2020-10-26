from enum import Enum


class ToolOri(Enum):
    X = 0
    Z = 90


class Tool:
    """
    Class to hold a lathe tool definition
    Tool String Formatting:
    Shape | Clearance Angle | Tolerance | Type | Edge Length | Thickness | Nose Radius | Direction
    Example Tool Definistion: DCMT070204R
    """
    def __init__(self, tool_string=None):
        self.tool_string = None             # DCMT070204R
        self.shape = None                   # D
        # clearance angle                   # C
        # tolerance                         # M
        # type                              # T
        self.length = None                  # 07
        # thickness                         # 02
        self.nose_radius = None             # 04
        self.direction = None               # R-L-N
        self.orientation = None             # orientation of the tool X or Z
        self.tool_rotation = 0              # tool rotation about tool tip

        if tool_string:
            self.set_tool(tool_string)

    def set_tool(self, tool_string, tool_ori=ToolOri.X, tool_rotation=0):

        if not len(tool_string) == 11:
            raise ValueError("Tool Input String Incomplete")

        # TODO: Validate the values passed in create a valid tool
        self.tool_string = tool_string
        self.shape = self.tool_string[0]
        self.length = self.tool_string[4:6]
        self.nose_radius = self.tool_string[8:10]
        self.direction = self.tool_string[-1]
        self.orientation = tool_ori
        self.tool_rotation = tool_rotation

        # for item in vars(self):
        #     print('item', getattr(self, item))

    def get_tool_cutting_angle(self):
        """
        Return the maximum cutting angle the tool is capable of
        Note: Angle is on the XZ plane and inverted. 
        """
        shapeAngle = self.getShapeAngle()
        rotation = self.getRotation()
        clearance = 2

        max_cutting_angle = 360 - (shapeAngle + rotation + clearance)

        # print('max_cutting angle:', max_cutting_angle)

        return max_cutting_angle

    def get_max_doc(self):
        """
        Return the maximum depth of cut (stepover) the tool is capable of
        """
        pass

    def getShapeAngle(self):
        """
        Return the angle of the tools shape
        """
        # TODO: Complete the shape angle dictionary
        shape = {
            "A": None,  # Parallelogram (85 degree)
            "B": None,  # Parallelogram (82 degree)
            "C": 80,    # Rhombic (80 degree)
            "D": 55,    # Rhombic (55 degree)
            "E": None,  # Rhombic (75 degree)
            "F": None,  # Rhombic (50 degree)
            "H": None,  # Hexagonal
            "K": None,  # Parallelogram (55 degree)
            "L": None, 	# Rectangular
            "M": None, 	# Rhombic (86 degree)
            "O": None, 	# Octagonal
            "P": None, 	# Pentagonal
            "R": 90, 	# Round
            "S": 90, 	# Square
            "T": 60, 	# Triangular
            "V": 35,    # Rhombic (35 degree)
            "W": 60, 	# Trigon
            "X": None   # Special Shape
        }

        angle = shape.get(self.shape, None)
        # print('shape Angle:', angle)
        return angle

    def getEdgeLength(self):
        """
        Return the edge length for the tool
        Sizes from: http://www.mitsubishicarbide.com/en/technical_information/tec_turning_tools/tec_turning_insert/tec_turning_guide/tec_turning_identification
        """
        shapeSize = {

            "C": {"03": 3.97, "04": 4.76, "05": 5.56, "06": 6.35, "08": 7.94, "09": 9.525, "12": 12.7, "16": 15.875, "19": 19.05, "22": 22.225, "25": 25.4},
            "D": {"04": 3.97, "05": 4.76, "06": 5.56, "07": 6.35, "09": 7.94, "11": 9.525, "15": 12.7, "19": 15.875, "23": 19.05},
            "R": {"06": 6.0, "08": 8.0, "09": 9.525, "10": 10, "12": 12.0, "16": 16, "20": 20, "25": 25},
            "S": {"03": 3.97, "04": 4.76, "05": 5.56, "06": 6.35, "08": 7.94, "09": 9.525, "12": 12.7, "16": 15.875, "19": 19.05, "22": 22.225, "25": 25.4},
            "T": {"08": 4.76, "09": 5.56, "11": 6.35, "13": 7.94, "16": 9.525, "22": 12.7, "27": 15.875, "33": 19.05, "38": 22.225, "44": 25.4},
            "V": {"08": 4.76, "09": 5.56, "11": 6.35, "13": 7.94, "16": 9.525, "22": 12.7},
            "W": {"02": 3.97, "L3": 4.76, "03": 5.56, "04": 6.35, "05": 7.94, "06": 9.525, "08": 12.7, "10": 15.875, "13": 19.05}

        }

        try:
            edgeLength = shapeSize[self.shape][self.length]
            # print("shape Size: ", edgeLength)
            return edgeLength
        except(KeyError):
            return None

    def getNoseRadius(self):
        """
        Return the nose radius for the tool
        """
        noseRadius = {
            "00": 0,  # sharp
            "V3": 0.03,
            "V5": 0.05,
            "01": 0.1,
            "02": 0.2,
            "04": 0.4,
            "08": 0.8,
            "12": 1.2,
            "16": 1.6,
            "20": 2.0,
            "24": 2.4,
            "28": 2.8,
            "32": 3.2
        }

        try:
            radius = noseRadius[self.nose_radius]
            # print("nose radius: ", radius)
            return radius
        except(KeyError):
            return None

    def getCuttingDirection(self):
        """
        Return the cutting angle defined for this tool
        R = Right [<-]
        L = Left  [->]
        N = Neutral
        """
        return self.direction

    def getRotation(self):
        """
        Return the tool rotation for this tool
        """
        return self.tool_rotation
