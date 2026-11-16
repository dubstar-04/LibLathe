import unittest

from liblathe.op.partoff import PartoffOP
from liblathe.gcode.command import Command
from liblathe.base.boundbox import BoundBox
from liblathe.base.point import Point
from liblathe.base.segment import Segment
from liblathe.tool.tool import Tool, ToolSide


class test_PartoffOP(unittest.TestCase):
    """Test for partoff_op.py"""

    def setUp(self):

        # Define Part Geometry
        partSegments = []

        PartPt1 = Point(0, 10)
        PartPt2 = Point(5, -9)
        PartPt3 = Point(9.5, -15.85)
        PartPt4 = Point(5.4, -22)
        PartPt5 = Point(5.4, -40)
        PartPt6 = Point(13, -45)
        PartPt7 = Point(13, -48)
        PartPt8 = Point(0, -48)

        partSegments.append(Segment(PartPt1, PartPt2, 0.75))
        partSegments.append(Segment(PartPt2, PartPt3))
        partSegments.append(Segment(PartPt3, PartPt4))
        partSegments.append(Segment(PartPt4, PartPt5))
        partSegments.append(Segment(PartPt5, PartPt6))
        partSegments.append(Segment(PartPt6, PartPt8))
        partSegments.append(Segment(PartPt7, PartPt8))

        # set feed rate to test
        self.hfeed = 10

        # Define Operations Properties
        params = {}
        params['allow_grooving'] = False
        params['finish_passes'] = 2
        params['stock_to_leave'] = 0
        params['hfeed'] = self.hfeed
        params['vfeed'] = 10

        self.op = PartoffOP()
        self.op.setParams(params)
        self.op.addPartSegments(partSegments)
        tool = Tool()
        tool.set_tool_from_string('DCMT070204R')
        self.op.add_tool(tool)

        # parting containment spans the kerf with its maximum Z on the part's back face
        width = tool.get_segmentgroup().boundbox().ZLength()
        self.op.add_containment(BoundBox(Point(0, -48 - width), Point(25, -48)))

    def test_getGCode(self):
        """run the operation and evaluate the gcode"""
        gcode = self.op.getGCode()

        # check there is a return list
        self.assertTrue(len(gcode))

        for command in gcode:

            # check the command is a liblathe.command.Command
            self.assertTrue(isinstance(command, Command))

            # check the command movement contains the a 'G'
            self.assertTrue(command.get_movement().startswith("G"))

            if command.get_movement() in ["G0", "G1", "G2", "G3"]:
                # rapids omit feed; cutting moves carry it
                feed_exists = "F" in command.getParams()
                self.assertEqual(feed_exists, command.get_movement() != "G0")

                # check the feed rate
                if feed_exists:
                    self.assertEqual(command.getParams()['F'], self.hfeed)


def parting_op(tool_z_min, sign=1, face=-20, kerf=2):
    """Return a parting op for a 2 mm wide square tool spanning Z [tool_z_min, tool_z_min + 2]."""
    op = PartoffOP()
    op.setParams({"clearance": 1})
    op.add_containment(BoundBox(Point(0, face - kerf), Point(sign * 15, face)))
    op.add_stock(BoundBox(Point(0, -25), Point(sign * 12, 1)))
    vertices = [(0, 0), (10, 0), (10, -20), (0, -20)]
    op.addPartSegments([Segment(Point(sign * x, z), Point(sign * u, v))
                        for (x, z), (u, v) in zip(vertices, vertices[1:])])
    vertices = [(0, tool_z_min), (0, tool_z_min + 2), (2, tool_z_min + 2), (2, tool_z_min), (0, tool_z_min)]
    tool = Tool()
    tool.set_tool_from_segments([Segment(Point(sign * x, z), Point(sign * u, v))
                                 for (x, z), (u, v) in zip(vertices, vertices[1:])])
    tool.side = ToolSide.NEAR if sign == 1 else ToolSide.FAR
    op.add_tool(tool)
    return op


class test_PartoffFace(unittest.TestCase):
    """The tool's +Z edge cuts on the containment's maximum Z, whatever its reference."""

    def test_tool_edge_on_face_for_each_reference(self):
        for reference, tool_z_min in (("left", -2), ("neutral", -1), ("right", 0)):
            for sign in (1, -1):
                with self.subTest(reference=reference, sign=sign):
                    op = parting_op(tool_z_min, sign)
                    tool_z_max = tool_z_min + 2
                    moves = [c.getParams() for c in op.getGCode()
                             if c.get_movement() in ("G0", "G1")]
                    feeds = [c.getParams() for c in op.getGCode() if c.get_movement() == "G1"]
                    self.assertTrue(feeds)
                    for position in feeds:
                        self.assertAlmostEqual(position["Z"] + tool_z_max, -20)
                    # no tool position within the part's radius crosses the face
                    for position in moves:
                        if sign * position["X"] < 12:
                            self.assertLessEqual(position["Z"] + tool_z_max, -20 + 1e-6)

    def test_face_inside_part_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "inside the part"):
            parting_op(-1, face=-19).getGCode()

    def test_face_beyond_part_is_allowed(self):
        feeds = [c.getParams() for c in parting_op(-1, face=-21).getGCode()
                 if c.get_movement() == "G1"]
        self.assertTrue(all(abs(position["Z"] + 22) < 1e-6 for position in feeds))

    def test_containment_narrower_than_tool_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least as wide"):
            parting_op(-1, kerf=1.5).getGCode()

    def test_reference_outside_tool_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Tool reference"):
            parting_op(0.5).getGCode()


if __name__ == '__main__':
    unittest.main()
