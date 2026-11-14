import unittest

from liblathe.gcode.command import Command, optimise_rapids


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
        params = command.getParams()
        self.assertEqual(params, self.params)

    def test_to_string(self):
        command = Command('G0')
        string = command.to_string()
        self.assertEqual(string, 'G0')

        command = Command('G0', self.params)
        string = command.to_string()
        self.assertEqual(string, 'G0 X-20 Y0 Z6 F10')

    def test_scientific_notation_is_expanded_without_changing_parameter_values(self):
        params = {'Z': -1e-7, 'K': 1e-6}
        command = Command('G33', params)
        self.assertEqual(command.to_string(), 'G33 Z-0.0000001 K0.000001')
        self.assertEqual(command.getParams(), params)

    def test_optimise_rapids_removes_feeds_stationary_and_collinear_moves(self):
        commands = [
            Command('G18'),
            Command('G0', {'X': 17, 'Z': 38, 'F': 500}),
            Command('G0', {'X': 17, 'Z': 0, 'F': 500}),
            Command('G0', {'X': 13, 'Z': 0, 'F': 500}),
            Command('G1', {'X': 13, 'Z': 35, 'F': 500}),
            Command('G0', {'X': 17, 'Z': 35, 'F': 500}),
            Command('G0', {'X': 17, 'Z': 38, 'F': 500}),
            Command('G0', {'X': 17, 'Z': 38, 'F': 500}),
            Command('G0', {'X': 17, 'Z': 0, 'F': 500}),
            Command('G0', {'X': 12, 'Z': 0, 'F': 500}),
        ]
        optimised = optimise_rapids(commands)
        self.assertEqual([(c.get_movement(), c.getParams()) for c in optimised], [
            ('G18', {}),
            ('G0', {'X': 17, 'Z': 38}),
            ('G0', {'X': 17, 'Z': 0}),
            ('G0', {'X': 13, 'Z': 0}),
            ('G1', {'X': 13, 'Z': 35, 'F': 500}),
            ('G0', {'X': 17, 'Z': 35}),
            ('G0', {'X': 17, 'Z': 0}),
            ('G0', {'X': 12, 'Z': 0}),
        ])
        self.assertEqual(commands[1].getParams()['F'], 500)

    def test_optimise_rapids_keeps_corners_and_cancelled_round_trips(self):
        commands = [
            Command('G1', {'X': 1, 'Z': 1, 'F': 10}),
            Command('G0', {'X': 2, 'Z': 1}),
            Command('G0', {'X': 2, 'Z': 2}),
            Command('G0', {'X': 2, 'Z': 3}),
            Command('G0', {'X': 2, 'Z': 2}),
            Command('G0', {'X': 2, 'Z': 3}),
            Command('G0', {'X': 2, 'Z': 1}),
        ]
        self.assertEqual([c.getParams() for c in optimise_rapids(commands)[1:]], [
            {'X': 2, 'Z': 1},
        ])

    def test_optimise_rapids_keeps_short_right_angle_corner(self):
        commands = [
            Command('G0', {'X': 0, 'Z': 0}),
            Command('G0', {'X': 0.0005, 'Z': 0}),
            Command('G0', {'X': 0.0005, 'Z': 0.0005}),
        ]

        optimised = optimise_rapids(commands)

        self.assertEqual([command.getParams() for command in optimised], [
            {'X': 0, 'Z': 0},
            {'X': 0.0005, 'Z': 0},
            {'X': 0.0005, 'Z': 0.0005},
        ])

    def test_optimise_rapids_merges_short_exactly_collinear_moves(self):
        commands = [
            Command('G0', {'X': 0, 'Z': 0}),
            Command('G0', {'X': 0.0005, 'Z': 0}),
            Command('G0', {'X': 0.001, 'Z': 0}),
        ]

        optimised = optimise_rapids(commands)

        self.assertEqual([command.getParams() for command in optimised], [
            {'X': 0, 'Z': 0},
            {'X': 0.001, 'Z': 0},
        ])


if __name__ == '__main__':
    unittest.main()
