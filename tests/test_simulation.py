import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import numpy as np
from lastmile.simulation import Config, simulate, load_demand
from lastmile.hourly import write_hourly
from lastmile.cli import write_csv
from lastmile.experiments import run_suite, interval
from lastmile.submission import main as package

class SimulationTests(unittest.TestCase):
    def test_conservation_capacity_and_reproducibility(self):
        counts = np.zeros((1,24,3), dtype=int)
        counts[0,0,0] = 30
        cfg = Config(fleet=1, capacity=3, window_hours=1)
        a = simulate(counts, cfg, trace=True)
        self.assertEqual(a, simulate(counts, cfg, trace=True))
        self.assertEqual(a['parcels'], 30)
        self.assertEqual(len({r['order_id'] for r in a['orders']}), 30)
        self.assertTrue(all(r['completion_hours'] >= r['arrival_hours'] for r in a['orders']))
        self.assertTrue(all(r['batch_size'] <= 3 for r in a['orders']))
        self.assertTrue(0 <= a['fleet_utilization'] <= 1)
        self.assertGreater(a['delay_rate'], 0)
        slower = simulate(counts, replace(cfg, speed_factor=.1, capacity_factor=.5))
        self.assertGreater(slower['avg_delivery_hours'], a['avg_delivery_hours'])
        self.assertEqual(slower['effective_capacity'], 1)

    def test_analytic_single_parcel_and_zero(self):
        counts = np.zeros((1,24,3), dtype=int)
        zero = simulate(counts, Config(fleet=1))
        self.assertEqual(zero['parcels'], 0)
        self.assertEqual(zero['fleet_utilization'], 0)
        counts[0,0,0] = 1
        cfg = Config(fleet=1, service_minutes=3)
        result = simulate(counts, cfg, trace=True)
        rng = np.random.default_rng(cfg.seed)
        arrival = rng.uniform(0,1,1)[0]
        xy = rng.uniform(-3,3,2)
        expected = np.ceil(arrival/.25)*.25-arrival+np.linalg.norm(xy)/18+.05
        self.assertAlmostEqual(result['avg_delivery_hours'], expected)
        self.assertAlmostEqual(result['fleet_utilization'], (2*np.linalg.norm(xy)/18+.05)/24)

    def test_import_suite_and_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/'normal.csv'
            daily = np.array([[[10,20,30]], [[12,15,20]]])
            rows = [{'date':'2026-01-01','promotion':0,'rain':0,'holiday':0}]
            write_hourly(path, rows, daily, 'normal')
            counts, meta = load_demand(path, 1)
            np.testing.assert_array_equal(counts.sum(axis=1), daily[1])
            self.assertEqual(meta['sample_id'], 1)
            with self.assertRaises(ValueError): load_demand(path, 2)
            out = root/'project'/'simulation'
            report = run_suite(path, out, Config(fleet=3), 2)
            self.assertEqual(len(report['summary']), 7)
            self.assertIsNotNone(report['summary']['normal']['delay_rate']['ci95_low'])
            self.assertTrue((out/'normal_orders_rep0.csv').is_file())
            package(['--results',str(root/'project'),'--out',str(root/'one.zip')])
            package(['--results',str(root/'project'),'--out',str(root/'two.zip')])
            self.assertEqual((root/'one.zip').read_bytes(), (root/'two.zip').read_bytes())
            # Duplicate, missing and negative hourly cells must be rejected.
            original = path.read_text()
            path.write_text(original+original.splitlines()[1]+'\n')
            with self.assertRaises(ValueError): load_demand(path)
            path.write_text('\n'.join(original.splitlines()[:-1])+'\n')
            with self.assertRaises(ValueError): load_demand(path,1)
            data = list(csv.DictReader(original.splitlines()))
            data[0]['parcels'] = '-1'
            with path.open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
            with self.assertRaises(ValueError): load_demand(path)
            path.write_text(original)
            cli = subprocess.run([sys.executable, '-m', 'lastmile.experiments', '--demand-csv', str(path), '--replications', '2', '--out', str(root/'cli')], capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            # Daily interface also retains exact totals.
            write_csv(root/'daily.csv', rows, daily[0], 'normal')
            expanded, _ = load_demand(root/'daily.csv')
            np.testing.assert_array_equal(expanded.sum(axis=1), daily[0])

    def test_invalid_config_and_counts(self):
        for kwargs in ({'fleet':0},{'capacity':1.5},{'speed_factor':0},{'window_hours':float('nan')}):
            with self.assertRaises(ValueError): Config(**kwargs)
        with self.assertRaises(ValueError): simulate(np.ones((24,3)))
        self.assertEqual(interval([1.,1.])['ci95_low'],1.)

if __name__ == '__main__': unittest.main()
