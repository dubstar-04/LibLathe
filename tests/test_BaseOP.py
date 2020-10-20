import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(os.path.dirname(thisFolder))
sys.path.append(parentFolder)
from LibLathe.LLBaseOP import BaseOP


class test_BaseOP(unittest.TestCase):
    """Test for LLBaseOP.py"""

    def setUp(self):
        self.baseop = BaseOP()
        self.props = {'min_dia': 0, 'extra_dia': 0, 'start_offset': 0, 'end_offset': 0, 'allow_grooving': False,
                      'allow_facing': False, 'allow_roughing': True, 'allow_finishing': True, 'step_over': 1,
                      'finish_passes': 2, 'hfeed': 10, 'vfeed': 10}

    def test_set_params(self):
        self.baseop.set_params(self.props)
        self.assertEqual(self.baseop.step_over, 1)
        self.assertEqual(self.baseop.hfeed, 10)
        self.assertEqual(self.baseop.vfeed, 10)
        self.assertTrue(self.baseop.allow_roughing)
        self.assertFalse(self.baseop.allow_facing)


if __name__ == '__main__':
    unittest.main()
