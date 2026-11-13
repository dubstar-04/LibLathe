import unittest

from liblathe.op.base import BaseOP, MachiningMode
from liblathe.op.partoff import PartoffOP
from liblathe.op.profile import ProfileOP
from liblathe.op.rough import RoughOP


class CuttingParameterTests(unittest.TestCase):
    def test_internal_mode_is_exposed_by_rough_and_profile_only(self):
        for operation in (RoughOP, ProfileOP):
            with self.subTest(operation=operation):
                op = operation()
                self.assertIs(op.getParams()["mode"], MachiningMode.EXTERNAL)
                op.setParams({"mode": MachiningMode.INTERNAL})
                self.assertIs(op.getParams()["mode"], MachiningMode.INTERNAL)
        for operation in (BaseOP, PartoffOP):
            with self.subTest(operation=operation):
                self.assertNotIn("mode", operation().getParams())

    def test_pass_offset_parameters(self):
        for operation in (BaseOP, RoughOP, ProfileOP, PartoffOP):
            with self.subTest(operation=operation):
                op = operation()
                self.assertEqual(op.pass_offset, 1.5)
                op.setParams({"pass_offset": 0.75})
                self.assertEqual(op.pass_offset, 0.75)
                self.assertEqual(op.getParams()["pass_offset"], 0.75)
                op.pass_offset = 0.25
                self.assertEqual(op.getParams()["pass_offset"], 0.25)

    def test_old_parameter_names_are_not_supported(self):
        for operation in (BaseOP, RoughOP, ProfileOP, PartoffOP):
            op = operation()
            for name in ("step_over", "radial_depth", "axial_depth", "finish_stepdown",
                         "radial_pass_offset", "axial_pass_offset"):
                with self.subTest(operation=operation, parameter=name):
                    self.assertFalse(hasattr(op, name))
                    self.assertNotIn(name, op.getParams())
                    with self.assertRaisesRegex(Warning, "undefined parameter"):
                        op.setParams({name: 1})

    def test_parting_ignores_pass_offset(self):
        from tests.op.test_partoff_op import test_PartoffOP

        fixture = test_PartoffOP()
        fixture.setUp()
        op = fixture.op
        expected = [command.to_string() for command in op.getGCode()]
        op.setParams({"pass_offset": 0})
        self.assertEqual([command.to_string() for command in op.getGCode()], expected)
