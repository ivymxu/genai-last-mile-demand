"""One-command demand generation, logistics experiments and reproducible reports."""
import argparse
from dataclasses import asdict, replace
import csv
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from scipy.stats import t
from .simulation import Config, load_demand, simulate


def interval(values):
    a = np.asarray(values, dtype=float)
    mean = float(a.mean())
    half = float(t.ppf(.975, len(a)-1)*a.std(ddof=1)/np.sqrt(len(a))) if len(a)>1 else None
    return {'mean': mean, 'ci95_low': mean-half if half is not None else None,
            'ci95_high': mean+half if half is not None else None, 'replications': len(a)}


def policies(base):
    return {'normal': base, 'surge': replace(base, demand_factor=1.3),
            'typhoon': replace(base, speed_factor=base.speed_factor*.55, capacity_factor=base.capacity_factor*.7),
            'surge_typhoon': replace(base, demand_factor=1.3, speed_factor=base.speed_factor*.55, capacity_factor=base.capacity_factor*.7),
            'fleet_minus20': replace(base, fleet=max(1, round(base.fleet*.8))),
            'fleet_plus20': replace(base, fleet=max(1, round(base.fleet*1.2))),
            'surge_fleet_plus15': replace(base, fleet=max(1, round(base.fleet*1.15)), demand_factor=1.3)}


def run_suite(source, out, base=Config(), replications=5):
    if replications < 2:
        raise ValueError('at least two replications required for uncertainty')
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('output directory must be empty')
    # Validate all requested demand paths before creating any result files.
    paths = [load_demand(source, i) for i in range(replications)]
    out.mkdir(parents=True, exist_ok=True)
    raw = []
    for rep, (counts, _) in enumerate(paths):
        for name, cfg in policies(base).items():
            result = simulate(counts, replace(cfg, seed=base.seed+rep), trace=(rep==0 and name=='normal'))
            trace = result.pop('orders', None)
            if trace is not None:
                write_rows(out/'normal_orders_rep0.csv', trace)
            raw.append({'scenario': name, 'replication': rep, **result})
    metrics = ('delay_rate', 'avg_delivery_hours', 'fleet_utilization', 'clearance_overtime_hours', 'parcels')
    summary = {name: {m: interval([r[m] for r in raw if r['scenario']==name]) for m in metrics} for name in policies(base)}
    paired = {}
    baseline = [r for r in raw if r['scenario']=='normal']
    for name in summary:
        if name == 'normal':
            continue
        other = [r for r in raw if r['scenario']==name]
        paired[name] = {m: interval([b[m]-a[m] for a,b in zip(baseline, other)]) for m in metrics[:3]}
    write_rows(out/'replications.csv', raw)
    write_rows(out/'summary.csv', [{'scenario': name, 'metric': m, **v} for name, ms in summary.items() for m,v in ms.items()])
    surge = [r for r in raw if r['scenario']=='surge']
    reserve = [r for r in raw if r['scenario']=='surge_fleet_plus15']
    reserve_difference = {m: interval([b[m]-a[m] for a,b in zip(surge, reserve)]) for m in metrics[:3]}
    report = {'data_kind': 'synthetic simulation; not observed logistics performance', 'summary': summary,
              'paired_difference_vs_normal': paired, 'reserve_difference_vs_surge': reserve_difference,
              'calibration': {'hypothetical_target': .15, 'tolerance': .02,
                              'normal_mean_within_target_band': abs(summary['normal']['delay_rate']['mean']-.15)<=.02,
                              'meaning': 'Internal target check only; does not establish real-world validity.'}}
    (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    lines = ['# Synthetic logistics experiment results', '', 'All values are model outputs under assumed operations, not historical measurements.', '',
             '| Scenario | Delay rate (95% t CI) | Mean delivery hours | Utilization |', '|---|---:|---:|---:|']
    for name, ms in summary.items():
        d = ms['delay_rate']
        lines.append(f"| {name} | {d['mean']:.2%} ({d['ci95_low']:.2%}, {d['ci95_high']:.2%}) | {ms['avg_delivery_hours']['mean']:.2f} | {ms['fleet_utilization']['mean']:.1%} |")
    lines += ['', 'Intervals describe replication uncertainty conditional on fixed assumptions. See results.json for paired differences.',
              '15% ±2 percentage points is a hypothetical calibration band, not measured history. No parameters are fitted to force that result.']
    lines += ['', f"Normal mean within hypothetical 13–17% band: {report['calibration']['normal_mean_within_target_band']}. A mismatch requires investigating assumptions, not claiming validation."]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    manifest = {'config': asdict(base), 'replications': replications, 'paths': [meta for _,meta in paths],
                'policies': {k: asdict(v) for k,v in policies(base).items()}, 'python': platform.python_version(),
                'versions': {name: __import__(name).__version__ for name in ('numpy','simpy','scipy','streamlit')},
                'input_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                'files_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir())}}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return report


def write_rows(path, rows):
    if not rows:
        return
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=Path('artifacts/project'))
    p.add_argument('--demand-csv', type=Path, help='normal daily/hourly CSV with sample IDs 0..replications-1')
    p.add_argument('--replications', type=int, default=5)
    p.add_argument('--horizon', type=int, default=3)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--fleet', type=int, default=48)
    p.add_argument('--capacity', type=int, default=24)
    p.add_argument('--window-hours', type=float, default=4.)
    p.add_argument('--service-minutes', type=float, default=3.)
    p.add_argument('--dispatch-minutes', type=float, default=15.)
    p.add_argument('--speed-factor', type=float, default=1.)
    p.add_argument('--model', choices=('statistical', 'cvae'), default='statistical')
    p.add_argument('--epochs', type=int, default=150)
    a = p.parse_args(argv)
    if a.replications < 2 or a.horizon < 1:
        p.error('replications >=2 and horizon >=1 required')
    if a.out.exists() and any(a.out.iterdir()):
        p.error('output directory must be empty')
    cfg = Config(fleet=a.fleet, capacity=a.capacity, window_hours=a.window_hours, seed=a.seed,
                 service_minutes=a.service_minutes, dispatch_minutes=a.dispatch_minutes, speed_factor=a.speed_factor)
    source = a.demand_csv
    if source is None:
        from .cli import main as demand_main
        demand_main(['--out', str(a.out/'demand'), '--hourly', '--samples', str(a.replications),
                     '--horizon', str(a.horizon), '--seed', str(a.seed), '--model', a.model, '--epochs', str(a.epochs)])
        source = a.out/'demand'/'normal_hourly.csv'
    report = run_suite(source, a.out/'simulation', cfg, a.replications)
    print((a.out/'simulation'/'REPORT.md').read_text())
    return None

if __name__ == '__main__':
    main()
