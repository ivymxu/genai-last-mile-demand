import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from lastmile.model import history, DemandModel, evaluate, calendar
from lastmile.cli import main

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.y = history(days=180)

    def test_history_reproducible_and_valid(self):
        r, y = history(days=180)
        self.assertEqual(r, self.rows)
        np.testing.assert_array_equal(y, self.y)
        self.assertEqual(y.shape, (180, 3))
        self.assertTrue((y >= 0).all())
        self.assertFalse(np.array_equal(y, history(days=180, seed=43)[1]))

    def test_sampling_and_scenario_effect(self):
        m = DemandModel().fit(self.rows, self.y)
        normal = m.sample(self.rows[:14], samples=30)
        np.testing.assert_array_equal(normal, m.sample(self.rows[:14], samples=30))
        surge = m.sample(self.rows[:14], samples=30, multiplier=1.3)
        self.assertTrue((surge >= normal).all())
        self.assertAlmostEqual(surge.mean()/normal.mean(), 1.3, places=3)
        self.assertGreater(normal.std(axis=0).mean(), 0)
        self.assertTrue((normal >= 0).all())
        with self.assertRaises(ValueError):
            m.sample(self.rows, multiplier=0)

    def test_holdout_not_used_in_fit(self):
        m, report = evaluate(self.rows[:140], self.y[:140], self.rows[140:], self.y[140:])
        m2, _ = evaluate(self.rows[:140], self.y[:140], self.rows[140:], self.y[140:]*2)
        np.testing.assert_array_equal(m.beta, m2.beta)
        self.assertTrue(0 <= report['generative']['coverage_90'] <= 1)
        self.assertTrue(np.isfinite(report['conditional_mean']['mae']))

    def test_model_roundtrip(self):
        m = DemandModel().fit(self.rows, self.y)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'model.npz'
            m.save(p)
            np.testing.assert_array_equal(m.sample(self.rows[:7]), DemandModel.load(p).sample(self.rows[:7]))

    def test_cli_reproducible_exports_and_protection(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a', Path(d)/'b'
            for p in (a, b):
                main(['--out', str(p), '--days', '90', '--samples', '5'])
            for name in ('history.csv', 'normal.csv', 'surge.csv', 'disruption.csv', 'metrics.json'):
                self.assertEqual((a/name).read_bytes(), (b/name).read_bytes())
            manifest = json.loads((a/'manifest.json').read_text())
            self.assertEqual(manifest['train_days'], 72)
            with self.assertRaises(SystemExit):
                main(['--out', str(a)])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            calendar('2024-01-01', 0, 1)
        with self.assertRaises(ValueError):
            DemandModel().fit(self.rows, -self.y)

if __name__ == '__main__':
    unittest.main()
