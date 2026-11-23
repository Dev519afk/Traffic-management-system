import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation_compare import compare

class SimulationTests(unittest.TestCase):
    def test_deterministic_and_safe(self):
        rates = {'North':.5,'East':.3,'South':.4,'West':.25}
        a = compare(180, rates, seed=5)
        b = compare(180, rates, seed=5)
        self.assertEqual(a,b)
        for info in a['policies'].values():
            self.assertEqual(info['arrived'], info['served'] + info['end_queue'])
            self.assertGreaterEqual(info['served'], 0)
            self.assertEqual(len(info['timeline']),180)

    def test_invalid_rates(self):
        with self.assertRaises(ValueError):
            compare(120, {'North':-1,'East':1,'South':1,'West':1})

if __name__ == '__main__': unittest.main()
