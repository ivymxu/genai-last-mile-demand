import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
import numpy as np
from lastmile.model import history
from lastmile.hourly import allocate_hourly, write_hourly, HEADER
from lastmile.validation import distribution_metrics


class HourlyTests(unittest.TestCase):
    def test_conservation_reproducibility_and_schema(self):
        rows, y = history(days=28)
        daily = np.stack([y, y+1])
        hourly = allocate_hourly(daily)
        np.testing.assert_array_equal(hourly.sum(axis=2), daily)
        np.testing.assert_array_equal(hourly, allocate_hourly(daily))
        self.assertFalse(np.array_equal(hourly, allocate_hourly(daily, 43)))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'hourly.csv'
            write_hourly(p, rows, daily, 'normal')
            with p.open() as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, HEADER)
                records = list(reader)
            self.assertEqual(len(records), 2*28*24*3)
            keys = {(r['sample_id'],r['date'],r['hour'],r['district']) for r in records}
            self.assertEqual(len(keys), len(records))
        with self.assertRaises(ValueError):
            allocate_hourly(daily+.5)

    def test_zero_demand_metrics(self):
        report = distribution_metrics(np.zeros((5,2,3)), np.zeros((2,3)))
        self.assertEqual(report['wape'], 0)


@unittest.skipUnless(importlib.util.find_spec('torch'), 'install neural extra')
class VAETests(unittest.TestCase):
    def test_training_roundtrip_and_reproducibility(self):
        from lastmile.vae import ConditionalVAE
        rows, y = history(days=90)
        m = ConditionalVAE().fit(rows[:72], y[:72], epochs=40)
        other = ConditionalVAE().fit(rows[:72], y[:72], epochs=40)
        self.assertTrue(np.isfinite(m.losses).all())
        self.assertLess(np.mean(m.losses[-10:]), np.mean(m.losses[:10]))
        draws = m.sample(rows[72:], 10)
        self.assertEqual(draws.shape, (10,18,3))
        np.testing.assert_array_equal(draws, other.sample(rows[72:],10))
        self.assertGreater(draws.std(axis=0).mean(), 0)
        self.assertTrue((m.sample(rows[72:],10,multiplier=1.3) >= draws).all())
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'vae.npz'
            m.save(p)
            np.testing.assert_array_equal(draws, ConditionalVAE.load(p).sample(rows[72:],10))
        report = distribution_metrics(draws, y[72:])
        self.assertTrue(0 <= report['coverage_90'] <= 1)
        # Evaluation only reads heldout observations; training arrays stay identical.
        before = m.center.copy()
        distribution_metrics(draws, y[72:]*2)
        np.testing.assert_array_equal(before, m.center)

    def test_cli_neural_hourly_repeat(self):
        from lastmile.cli import main
        with tempfile.TemporaryDirectory() as d:
            for name in ('a','b'):
                main(['--out',str(Path(d)/name),'--model','cvae','--epochs','5',
                      '--hourly','--days','90','--horizon','2','--samples','2'])
            for name in ('normal.csv','normal_hourly.csv','metrics.json','manifest.json'):
                self.assertEqual((Path(d)/'a'/name).read_bytes(), (Path(d)/'b'/name).read_bytes())
