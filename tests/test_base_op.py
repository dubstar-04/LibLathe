import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.base_op import BaseOP


class test_BaseOP(unittest.TestCase):
    """Test for base_op.py"""

    def setUp(self):
        self.baseop = BaseOP()
        self.setProps = {'min_dia': 0, 'extra_dia': 0, 'start_offset': 0, 'end_offset': 0, 'allow_grooving': False, 
                        'step_over': 1, 'finish_passes': 2, 'stock_to_leave': 0.25, 'hfeed': 10, 'vfeed': 10}
        self.getProps = {'min_dia': 0, 'extra_dia': 0, 'start_offset': 0, 'end_offset': 0, 'allow_grooving': False,
                        'step_over': 1.5, 'finish_passes': 2, 'stock_to_leave': 0, 'hfeed': 100, 'vfeed': 50}

    def test_set_params(self):
        self.baseop.set_params(self.setProps)
        self.assertEqual(self.baseop.step_over, 1)
        self.assertEqual(self.baseop.hfeed, 10)
        self.assertEqual(self.baseop.vfeed, 10)
        self.assertFalse(self.baseop.allow_grooving)

    @unittest.expectedFailure
    def test_set_params_error(self):
        # Test get_gcode() with no tool set

        params = {}
        params['wrong_para'] = "error"

        self.test_base_op = BaseOP()

        with self.assertWarns(Warning):
            self.test_base_op.set_params(params)

    @unittest.expectedFailure
    def test_get_gcode(self):
        # Test get_gcode() with no tool set
        with self.assertWarns(Warning):
            self.baseop.get_gcode()

    def test_generate_gcode(self):
        gcode = self.baseop.generate_gcode()
        self.assertEqual(gcode, "")

    def test_get_params(self):
        params = self.baseop.get_params()
        for i in params:
            self.assertEqual(params[i], self.getProps[i])


if __name__ == '__main__':
    unittest.main()
