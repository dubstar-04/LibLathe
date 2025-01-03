""" Tool Class """
from enum import Enum
import math

from liblathe.base.point import Point
from liblathe.base.segmentgroup import SegmentGroup
from liblathe.base.segment import Segment


class ToolOri(Enum):
    """ Tool Orientation """
    X = 0
    Z = 90


class Tool:
    """
    Class to hold a lathe tool definition
    Tool String Formatting:
    Shape | Clearance Angle | Tolerance | Type | Edge edge_length | Thickness | Nose Radius | Direction
    Example Tool Definition: DCMT070204R

    Tool shape is stored as a SegmentGroup()
    """
    def __init__(self, tool_string=None):
        # tool_string                       # DCMT070204R
        self.shape = None                   # D
        # clearance angle                   # C
        # tolerance                         # M
        # type                              # T
        self.tip_angle = None
        self.edge_length = None             # 07
        # thickness                         # 02
        self.nose_radius = None             # 04
        self.direction = None               # R-L-N
        self.orientation = ToolOri.X        # orientation of the tool X or Z
        self.tool_rotation = 0              # tool rotation about tool tip
        self.segment_group = SegmentGroup()  # tool shape

        if tool_string:
            self.set_tool_from_string(tool_string)

    def set_tool_from_string(self, tool_string):
        """Set the tools shape from a string"""

        if not len(tool_string) == 11:
            raise ValueError("Tool Input String Incomplete")

        # TODO: Validate the values passed in create a valid tool
        self.shape = tool_string[0]
        edge_length = tool_string[4:6]
        radius = tool_string[8:10]

        self.tip_angle = self.get_tip_angle_from_shape(self.shape)
        self.edge_length = self.get_edge_length(self.shape, edge_length)
        self.nose_radius = self.get_nose_radius(radius)
        self.direction = tool_string[-1]

        self.set_segmentgroup_from_string()

    def set_tool_from_segments(self, segments):
        """Set the tools shape from segments"""
        for segment in segments:
            self.segment_group.addSegment(segment)

    def get_segmentgroup(self):
        """
        Return a segment group for the shape
        """

        # if the tool has a rotation apply the rotation to the segment group
        if self.tool_rotation != 0:
            return self.rotate_tool_shape()

        # return the segment group
        return self.segment_group

    def getToolShape(self):
        """
        Return the tool's shape.

        The tool shape is a string that describes the geometry of the turning tool.
        It can include details such as the type of tool (e.g., round, square, diamond)

        The shape is represented by a single character such as: C, D, S, V, R, T
        the shape is the first character in the tool string which can typically be
        11 characters long and found on the inserts packaging.

        Returns:
            str: A string representing the shape of the turning tool.
        """
        return self.shape

    def set_tool_shape(self, shape):
        """
        Set the tools shape
        """

        if shape in ["C", "D", "S", "V", "R", "T"]:
            self.shape = shape
        else:
            raise Warning("Tool shape not valid")

    def set_tip_angle(self, angle):
        """Set the tools tip angle"""

        if (isinstance(angle, int) or isinstance(angle, float)) and angle > 0 and angle < 90:
            self.tip_angle = angle
        else:
            raise Warning("Tool tip angle must be a number [0 - 90]")

    def set_edge_length(self, edge_length):
        """Set the tools edge edge_length"""

        if (isinstance(edge_length, int) or isinstance(edge_length, float)) and edge_length > 0:
            self.edge_length = edge_length
        else:
            raise Warning("Tool edge length must be a number > 0")

    def set_nose_radius(self, radius):
        """Set the tools nose radius"""

        if (isinstance(radius, int) or isinstance(radius, float)) and radius > 0:
            self.nose_radius = radius
        else:
            raise Warning("Tool nose radius must be a number > 0")

    def set_direction(self, direction):
        """ Set the tools cutting direction R-N-L"""
        direction = direction.upper()
        if direction in ["R", "N", "L"]:
            self.direction = direction
        else:
            raise Warning("Tool direction not valid")

    def set_rotation(self, rotation):
        """ Set the tools cutting rotation"""

        if (isinstance(rotation, int) or isinstance(rotation, float)) and rotation > 0 and rotation < 360:
            self.tool_rotation = rotation
        else:
            raise Warning("Tool rotation must be a number [0 - 360]")

    def set_orientation(self, orientation):
        """ Set the tools cutting rotation"""
        if orientation in [ToolOri.X, ToolOri.Z]:
            self.orientation = orientation
        else:
            raise Warning("Tool orientation not valid")

    def get_tip_angle_from_shape(self, shape_char):
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

        angle = shape.get(shape_char, None)
        # print('shape Angle:', angle)
        return angle

    def get_edge_length(self, shape, edge_length):
        """
        Return the edge length for the tool
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

        if shape in shapeSize:
            try:
                edge_length = shapeSize[shape][edge_length]
                # print("shape Size: ", edgeedge_length)
                return edge_length
            except KeyError:
                raise Warning("Tool length code not valid")
        else:
            raise Warning("Tool shape not valid")

    def get_nose_radius(self, radius):
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
            radius = noseRadius[radius]
            # print("nose radius: ", radius)
            return radius
        except KeyError:
            raise Warning("Tool radius not valid")

    def get_cutting_direction(self):
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

    def rotate_tool_shape(self):
        """
        Rotate the tools shape by the defined rotation

        Returns:
            SegmentGroup: The rotated segment group
        """

        segment_group = self.get_segmentgroup()
        rotated_segment_group = SegmentGroup()
        angle = math.radians(self.getRotation())

        for segment in segment_group.getSegments():
            start = segment.start.rotate(Point(), angle)
            end = segment.end.rotate(Point(), angle)
            rotated_segment_group.addSegment(Segment(start, end, segment.bulge))

        return rotated_segment_group


    def set_segmentgroup_from_string(self):
        """
        Return a segment group for the shape
        """

        # TODO: Support other tool shapes

        # 4 sided shapes
        if self.shape in ["C", "D", "S", "V"]:
            self.get_segmentgroup_from_string_rectangle()
            return

        # curcular shapes
        if self.shape in ["R"]:
            self.get_segmentgroup_from_string_round()
            return

        # triangle shapes
        if self.shape in ["T"]:
            self.get_segmentgroup_from_string_triangle()
            return

        raise ValueError("The defined tool shape is not currently supported")

    def get_segmentgroup_from_string_rectangle(self):
        """Get a 4 sided tool shape from the tool string"""
        shape_group = SegmentGroup()

        ang = 270 - self.tip_angle / 2
        start_point = Point()
        pt2 = start_point.project(math.radians(ang), self.edge_length)

        ang += self.tip_angle
        pt3 = pt2.project(math.radians(ang), self.edge_length)

        ang += 180 - self.tip_angle
        pt4 = pt3.project(math.radians(ang), self.edge_length)

        seg1 = Segment(start_point, pt2)
        seg2 = Segment(pt2, pt3)
        seg3 = Segment(pt3, pt4)
        seg4 = Segment(pt4, start_point)

        shape_group.addSegment(seg1)
        shape_group.addSegment(seg2)
        shape_group.addSegment(seg3)
        shape_group.addSegment(seg4)

        # Debug().draw([shape_group])

        self.segment_group = shape_group

    def get_segmentgroup_from_string_round(self):
        """Get the parts shape from the tool string"""
        shape_group = SegmentGroup()

        half_edge_length = self.edge_length * 0.5

        center_point = Point(0, half_edge_length)
        start_point = Point(center_point.X + half_edge_length, center_point.Z)
        end_point = Point(center_point.X - half_edge_length, center_point.Z)

        seg1 = Segment(start_point, end_point, 1)
        seg2 = Segment(end_point, start_point, 1)

        shape_group.addSegment(seg1)
        shape_group.addSegment(seg2)

        self.segment_group = shape_group

    def get_segmentgroup_from_string_triangle(self):
        """Get the parts shape from the tool string"""
        shape_group = SegmentGroup()
        ang = 270 - self.tip_angle / 2
        start_point = Point()
        pt2 = start_point.project(math.radians(ang), self.edge_length)

        ang += self.tip_angle * 2
        pt3 = pt2.project(math.radians(ang), self.edge_length)

        seg1 = Segment(start_point, pt2)
        seg2 = Segment(pt2, pt3)
        seg3 = Segment(pt3, start_point)

        shape_group.addSegment(seg1)
        shape_group.addSegment(seg2)
        shape_group.addSegment(seg3)

        self.segment_group = shape_group
