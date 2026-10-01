"""Run with NumPy installed: python3 tests/check_plot_units.py."""
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from field_csv import load_field_csv


class PlotUnitsTest(unittest.TestCase):
    def test_mm_and_legacy_cm_are_equivalent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'field.csv'
            for unit, coordinates in [('mm', '100,20,10'), ('cm', '10,2,1')]:
                path.write_text(f'x_{unit},y_{unit},z_{unit},Ez_V_per_cm,status\n{coordinates},-4200,0\n')
                data = load_field_csv(path)
                self.assertEqual(data['x_mm'][0], 100)
                self.assertEqual(data['y_mm'][0], 20)
                self.assertEqual(data['z_mm'][0], 10)
                self.assertEqual(data['Ez_V_per_cm'][0], -4200)

    def test_ambiguous_units_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'field.csv'
            path.write_text('x_mm,y_cm,z_mm\n1,2,3\n')
            with self.assertRaises(ValueError):
                load_field_csv(path)


if __name__ == '__main__':
    unittest.main()
