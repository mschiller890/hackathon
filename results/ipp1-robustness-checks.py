"""Regression checks for lane R. Synthetic fixtures only; no experimental data."""
import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))


class ExperimentChecks(unittest.TestCase):
    def module(self, name):
        self.assertIsNotNone(importlib.util.find_spec(name), f"Missing implementation: {name}")
        return importlib.import_module(name)

    def test_drift_is_linear_within_discharge_and_does_not_mutate_input(self):
        mod = self.module("ipp1_robustness")
        x = np.zeros((6, 2), dtype=np.float32)
        g = np.array([4, 4, 4, 8, 8, 8])
        t = np.array([0, .5, 1, 0, .5, 1])
        got = mod.corrupt(x, g, t, np.ones(2), 0, .2, 17)
        np.testing.assert_allclose(got[[0, 3]], 0)
        np.testing.assert_allclose(got[[1, 4]] * 2, got[[2, 5]])
        self.assertFalse(np.allclose(got[2], got[5]))
        np.testing.assert_array_equal(x, 0)
        np.testing.assert_array_equal(got, mod.corrupt(x, g, t, np.ones(2), 0, .2, 17))
        np.testing.assert_array_equal(mod.corrupt(x, g, t, np.ones(2), 0, 0, 17), x)

    def test_whole_group_subsets_are_nested_and_exclude_test_groups(self):
        mod = self.module("ipp1_learning_curve")
        g = np.repeat(np.arange(10), 3)
        train = np.arange(24)
        small = mod.training_subset(train, g, .25, 12)
        large = mod.training_subset(train, g, .5, 12)
        self.assertEqual(len(np.unique(g[small])), 2)
        self.assertEqual(len(np.unique(g[large])), 4)
        self.assertTrue(set(small) <= set(large) <= set(train))
        for group in np.unique(g[large]):
            self.assertEqual(np.count_nonzero(g[large] == group), 3)
        np.testing.assert_array_equal(mod.training_subset(train, g, 1, 12), train)

    def test_history_is_causal_sorted_and_never_crosses_discharge(self):
        mod = self.module("ipp1_temporal")
        g = np.array([2, 1, 2, 1, 1])
        t = np.array([.2, .3, .1, .1, .2])
        idx = mod.history_indices(g, t, 3)
        np.testing.assert_array_equal(idx, [[2, 2, 0], [3, 4, 1], [2, 2, 2],
                                            [3, 3, 3], [3, 3, 4]])
        self.assertTrue(np.all(g[idx] == g[:, None]))
        self.assertTrue(np.all(t[idx] <= t[:, None]))
        np.testing.assert_array_equal(idx[:, -1], np.arange(5))
        with self.assertRaises(ValueError):
            mod.history_indices(np.array([1, 1]), np.array([0., 0.]), 3)

    def test_jitter_measures_error_changes_not_smoothness_alone(self):
        mod = self.module("ipp1_temporal")
        g = np.array([1, 1, 2, 2])
        t = np.array([0., 1., 0., 1.])
        y = np.tile(np.array([0., 1., 100., 101.])[:, None], (1, 16))
        mask = np.ones_like(y, dtype=bool)
        perfect = mod.step_errors(y, y, mask, g, t)
        fixed = mod.step_errors(np.zeros_like(y), y, mask, g, t)
        self.assertEqual(perfect["R_mag_axis"]["error_step_mae"], 0)
        self.assertEqual(fixed["R_mag_axis"]["error_step_mae"], 1000)
        self.assertEqual(fixed["R_mag_axis"]["pairs"], 2)


if __name__ == "__main__":
    unittest.main()
