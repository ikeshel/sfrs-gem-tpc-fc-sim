"""Voltage interpolation and boundary safety checks, independent of Garfield++."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('electrodes', Path(__file__).resolve().parents[1] / 'scripts/electrode_voltages.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ElectrodesTest(unittest.TestCase):
    def config(self):
        return dict(cathode_V=-200, anode_V=4000, position_unit='relative', positions=list(range(7)))

    def test_equal(self):
        self.assertEqual([v for _, _, v in module.potentials(self.config())],
                         [-200, 500, 1200, 1900, 2600, 3300, 4000])

    def test_unequal_and_reversed_coordinates(self):
        cfg = self.config()
        cfg['positions'] = [12, 11, 9, 7, 5, 2, 0]
        cfg['position_unit'] = 'mm'
        rows = module.potentials(cfg)
        self.assertEqual(rows[1][2], 150)
        self.assertEqual(rows[-1][2], 4000)

    def test_bad_positions(self):
        for positions in ([0]*7, [0, 1], [0, 1, 3, 2, 4, 5, 6]):
            cfg = self.config()
            cfg['positions'] = positions
            with self.assertRaises(ValueError):
                module.potentials(cfg)

    def test_boundary_mapping(self):
        rows = module.potentials(self.config())
        mapping = {name: [i] for i, name in enumerate(module.NAMES, 10)}
        result = module.boundary_blocks(rows, mapping)
        self.assertIn('Target Boundaries(1) = 10', result)
        self.assertIn('Potential = -200', result)
        self.assertIn('Potential = 4000', result)
        mapping['anode'] = [10]
        with self.assertRaises(ValueError):
            module.boundary_blocks(rows, mapping)
        mapping['anode'] = []
        with self.assertRaises(ValueError):
            module.boundary_blocks(rows, mapping)


if __name__ == '__main__':
    unittest.main()
