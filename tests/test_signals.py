import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from signal_controller import SignalController, DIRECTIONS, choose_green


class SignalControllerTests(unittest.TestCase):
    def setUp(self):
        self.demand = {'North':15,'East':8,'South':3,'West':6}

    def test_thresholds(self):
        self.assertEqual([choose_green(n) for n in [0,4,5,11,12,300]], [20,20,30,30,45,45])
        with self.assertRaises(ValueError): choose_green(-1)

    def test_timing_and_clearance(self):
        c = SignalController.start(self.demand)
        self.assertEqual((c.active,c.state,c.remaining), ('North','GREEN',45))
        c.tick({'North':999,'East':8,'South':3,'West':6}, seconds=44)
        self.assertEqual(c.remaining, 1)   # New arrivals do not reset the active GREEN timer
        c.tick(self.demand)
        self.assertEqual((c.state,c.remaining), ('YELLOW',3))
        c.tick(self.demand,seconds=3)
        self.assertEqual((c.state,c.remaining), ('ALL_RED',2))
        self.assertTrue(all(s == 'RED' for s in c.lights().values()))
        c.tick(self.demand,seconds=2)
        self.assertEqual((c.active,c.state,c.remaining),('East','GREEN',30))

    def test_never_two_green_and_all_get_turn(self):
        c = SignalController.start(self.demand)
        seen = set()
        for _ in range(500):
            lights = c.lights()
            self.assertLessEqual(sum(v == 'GREEN' for v in lights.values()),1)
            for d in DIRECTIONS:
                if lights[d] == 'GREEN': seen.add(d)
            c.tick(self.demand)
        self.assertEqual(seen, set(DIRECTIONS))

    def test_invalid_demand_rejected_before_changing_state(self):
        c = SignalController.start(self.demand)
        before = (c.active,c.state,c.remaining)
        with self.assertRaises(ValueError):
            c.tick({'North':-5,'East':8,'South':3,'West':6})
        self.assertEqual((c.active,c.state,c.remaining),before)


if __name__ == '__main__':
    unittest.main()
