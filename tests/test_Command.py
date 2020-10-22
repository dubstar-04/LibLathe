import os
import sys
import unittest

thisFolder = os.path.dirname(os.path.abspath(__file__))
parentFolder = os.path.dirname(thisFolder)
sys.path.append(parentFolder)
from liblathe.command import Command


class test_command(unittest.TestCase):
    """Test for command.py"""
    def setUp(self):
        self.params = {'X': -20, 'Y': 0, 'Z': 6, 'F': 10}

    def test_get_movement(self):
        command = Command('G0')
        movement = command.get_movement()
        self.assertEqual(movement, 'G0')

    def test_params(self):
        command = Command('G0', self.params)
        params = command.get_params()
        self.assertEqual(params, self.params)

    def test_to_string(self):
        command = Command('G0')
        string = command.to_string()
        self.assertEqual(string, 'G0')

        command = Command('G0', self.params)
        string = command.to_string()
        self.assertEqual(string, 'G0 X-20 Y0 Z6 F10')


if __name__ == '__main__':
    unittest.main()
