"""One-command reproducible experiment and teammate CSV export."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from .model import DISTRICTS, history, calendar, evaluate


def write_csv(path, rows, y, scenario, sample=0):
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "district", "parcels", "promotion", "rain", "holiday", "scenario", "sample_id"])
        for row, counts in zip(rows, y):
            for district, count in zip(DISTRICTS, counts):
                writer.writerow([row["date"], district, int(count), row["promotion"], row["rain"], row["holiday"], scenario, sample])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", choices=("statistical", "cvae"), default="statistical")
    p.add_argument("--epochs", type=int, default=150)
    p.add_argument("--hourly", action="store_true", help="also export assumed hourly allocations")
    p.add_argument("--out", type=Path, default=Path("artifacts"))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--days", type=int, default=730)
    p.add_argument("--horizon", type=int, default=14)
    p.add_argument("--samples", type=int, default=200)
    a = p.parse_args(argv)
    if a.epochs < 1 or a.days < 90 or a.horizon < 1 or a.samples < 2 or a.seed < 0:
        p.error("days >=90, horizon >=1, samples >=2, seed >=0 required")
    if a.model == "cvae":
        try:
            from .vae import ConditionalVAE
        except ImportError:
            p.error("CVAE requires installing the neural extra: pip install -e .[neural]")
    if a.out.exists() and any(a.out.iterdir()):
        p.error("output directory must be empty to protect previous results")
    a.out.mkdir(parents=True, exist_ok=True)
    rows, y = history(days=a.days, seed=a.seed)
    cut = int(.8*a.days)
    _, metrics = evaluate(rows[:cut], y[:cut], rows[cut:], y[cut:], a.seed)
    # Refit only after held-out evaluation, for future scenario generation.
    from .model import DemandModel
    model = DemandModel().fit(rows, y)
    if a.model == "cvae":
        evaluated = ConditionalVAE().fit(rows[:cut], y[:cut], a.epochs, a.seed)
        from .validation import distribution_metrics
        metrics["cvae"] = distribution_metrics(evaluated.sample(rows[cut:], 500, a.seed), y[cut:])
        metrics["cvae"]["training_loss"] = {"first": evaluated.losses[0], "last": evaluated.losses[-1]}
        model = ConditionalVAE().fit(rows, y, a.epochs, a.seed)
    model.save(a.out / "model.npz")
    write_csv(a.out / "history.csv", rows, y, "synthetic_history")
    from datetime import date, timedelta
    future = calendar((date.fromisoformat(rows[-1]["date"])+timedelta(days=1)).isoformat(), a.horizon, a.seed+2)
    from .hourly import write_hourly
    if a.hourly:
        write_hourly(a.out / "history_hourly.csv", rows, y[None], "synthetic_history", a.seed)
    metrics["scenarios"] = {}
    for name, multiplier in (("normal", 1.), ("surge", 1.3), ("disruption", .8)):
        draws = model.sample(future, a.samples, a.seed, multiplier)
        if a.hourly:
            write_hourly(a.out / f"{name}_hourly.csv", future, draws, name, a.seed+3)
        # Shared random numbers isolate scenario multiplier effects.
        with (a.out / f"{name}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "district", "parcels", "promotion", "rain", "holiday", "scenario", "sample_id"])
            for s, path in enumerate(draws):
                for row, counts in zip(future, path):
                    for district, count in zip(DISTRICTS, counts):
                        w.writerow([row["date"], district, int(count), row["promotion"], row["rain"], row["holiday"], name, s])
        metrics["scenarios"][name] = {"mean_daily_total": float(draws.sum(axis=2).mean()), "multiplier": multiplier}
    (a.out/"metrics.json").write_text(json.dumps(metrics, indent=2)+"\n")
    manifest = {"model": a.model, "epochs": a.epochs if a.model == "cvae" else None,
                "hourly_profile": "assumed two-peak multinomial" if a.hourly else None,
                "torch": __import__("torch").__version__ if a.model == "cvae" else None, "seed": a.seed, "days": a.days, "horizon": a.horizon, "samples": a.samples,
                "train_days": cut, "test_days": a.days-cut, "python": platform.python_version(),
                "numpy": np.__version__, "data_kind": "fully synthetic; no real company data",
                "sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                           for f in sorted(a.out.iterdir()) if f.suffix != ".npz"}}
    (a.out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
