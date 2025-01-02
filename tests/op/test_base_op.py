import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
opFolder = os.path.dirname(thisFolder)
parentFolder = os.path.dirname(opFolder)
sys.path.append(parentFolder)

from liblathe.op.base import BaseOP


class test_BaseOP(unittest.TestCase):
    """Test for op.py"""

    def setUp(self):
        self.baseop = BaseOP()
        self.setProps = {'allow_grooving': False, 'step_over': 1, 'finish_passes': 1, 'stock_to_leave': 0.25, 'hfeed': 10, 'vfeed': 10, 'clearance': 4}
        self.getProps = {'allow_grooving': False, 'step_over': 1.5, 'finish_passes': 1, 'stock_to_leave': 0, 'hfeed': 100, 'vfeed': 50, 'clearance': 3}

    def test_setParams(self):
        self.baseop.setParams(self.setProps)
        self.assertEqual(self.baseop.step_over, 1)
        self.assertEqual(self.baseop.hfeed, 10)
        self.assertEqual(self.baseop.vfeed, 10)
        self.assertFalse(self.baseop.allow_grooving)

    @unittest.expectedFailure
    def test_setParams_error(self):
        # Test getGCode() with no tool set

        params = {}
        params['wrong_para'] = "error"

        self.test_op = BaseOP()

        with self.assertWarns(Warning):
            self.test_op.setParams(params)

    @unittest.expectedFailure
    def test_getGCode(self):
        # Test getGCode() with no tool set
        with self.assertWarns(Warning):
            self.baseop.getGCode()

    def test_generate_gcode(self):
        gcode = self.baseop.generateGCode()
        self.assertEqual(gcode, "")

    def test_getParams(self):
        params = self.baseop.getParams()
        for i in params:
            self.assertEqual(params[i], self.getProps[i])


if __name__ == '__main__':
    unittest.main()
