import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.plot import Plot


class test_Plot(unittest.TestCase):
    """Test for LLPlot.py"""

    def setUp(self):
        self.plot = Plot()

    @unittest.expectedFailure
    def test_set_file_path_should_raise_warning(self):
        with self.assertWarns(Warning):
            self.plot.set_file_path('test')


if __name__ == '__main__':
    unittest.main()
