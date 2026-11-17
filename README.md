# ISE450: GenAI-assisted last-mile delivery simulation

This project studies how synthetic demand, operational disruption and fleet size
affect a simplified Hong Kong delivery operation. It combines reproducible demand
generation, a SimPy discrete-event simulator, replicated scenario experiments and
an interactive Streamlit dashboard. All demand and operating parameters are
synthetic assumptions; results are conditional simulation findings, not measured
company performance.

## System architecture

```text
Synthetic history (3 districts, calendar/context)
    └─ Chronological fit/evaluation → refit demand generator
           ├─ Statistical regression + residual resampling (default)
           └─ Conditional VAE (optional neural model)
                  ↓ daily counts → assumed hourly allocation → CSV paths
           SimPy parcels → district queues → vehicle batches → deliveries
                  ↓ normal / surge / typhoon / fleet-policy experiments
           Replication metrics → 95% intervals, paired comparisons, manifests

Streamlit dashboard → same simulator, interactive single-run controls and exports
Submission packager → source, tests, documentation, run inputs/results and hashes
```

Implementation: `model.py`, `vae.py`, `hourly.py` and `cli.py` generate demand;
`simulation.py` models operations; `experiments.py` runs comparisons;
`dashboard.py` supplies the UI; `submission.py` builds a reproducible ZIP.

## Methodology

The default demand generator learns from 730 synthetic days across Hong Kong
Island, Kowloon and the New Territories. Evaluation uses the first 80% of dates
for training and the last 20% for testing, with a weekday-average baseline. Ridge
regression of log counts and joint residual block resampling generate daily
paths. The optional CVAE is a separate neural alternative. Hourly allocation is
an assumed profile, not learned from hourly observations.

The simulator creates parcels with uniform within-hour arrivals, queues them by
district and checks for dispatch every 15 minutes. The oldest waiting district
receives the nearest idle vehicle, loaded to capacity. Nearest-neighbour delivery
stops incur travel plus service time, followed by a return to the depot. Runs
start empty and continue through queue clearance after the arrival horizon.

The base configuration has 48 vehicles, 24 parcels/batch, a four-hour delivery
window and three minutes of service per stop. District speeds are 18/22/28 km/h.
Distances are Euclidean and operations run 24/7, without shifts, traffic changes,
loading time or breakdowns. Full equations, geometry, uncertainty methods and
limitations are in [Methodology](docs/METHODOLOGY.md).

## Installation

Use Python 3.11–3.13. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

To run the optional neural model and **all** tests, install its extra:

```sh
python -m pip install -e '.[neural]'
python -m unittest discover -s tests -v
```

The neural tests skip when PyTorch is absent. No API keys or company dataset are
required. Execution is offline after dependencies are installed.

## Final simulation experiment

The recorded final run uses **20 replications, a seven-day arrival horizon and
seed 42**, with the statistical generator. To reproduce it in a new directory:

```sh
lastmile-project --out artifacts/final-reproduction --replications 20 --horizon 7 --seed 42
```

The seven policies are normal, +30% demand surge, typhoon (speed ×0.55 and batch
capacity ×0.70), combined surge/typhoon, ±20% fleet and +15% reserve fleet under
surge. Counts/capacities/fleets are rounded as documented. Results include
replication CSVs, summary means and 95% Student-t intervals, paired policy
comparisons, a normal replication-0 parcel trace and provenance manifests.

The archived final inputs and outputs are in [examples/final-run](examples/final-run).
Earlier [demand](examples/default-run) and [five-replication logistics](examples/logistics-run)
examples are preserved unchanged as historical runs, not relabeled as final.
The CLI's small defaults remain five replications/three days: use the explicit
command above for the final design. Existing results are never overwritten;
choose a new empty destination for each execution.

To reuse a complete daily or hourly CSV with sample IDs 0–19:

```sh
lastmile-project --demand-csv path/to/normal_hourly.csv --replications 20 --seed 42 --out artifacts/imported
```

Imported CSV dates determine the horizon; `--horizon` only controls generated
inputs. Check the input path spans seven days when reproducing the final design.
For demand-only exports use `lastmile --hourly --out artifacts/demand`. To use the
optional CVAE, add `--model cvae --epochs 150` to either generation command; that
creates a different experiment and is not the source of the final results below.

## Dashboard

```sh
streamlit run src/lastmile/dashboard.py
```

Open the local address printed by Streamlit, select scenarios, adjust controls
and click **Run simulation**. The UI displays delay rate, average delivery time,
fleet utilization, scenario charts, district outcomes and downloadable metrics
and parcel traces. It also accepts CSV uploads.

Dashboard defaults are a **single replication**, two generated days, 365 days of
synthetic training history and seed 42. They intentionally differ from the final
CLI experiment. Dashboard screenshots are demonstrations, not substitutes for the
replicated results or their confidence intervals.

## Key findings

The final statistical run produces the following means:

| Scenario | Delay rate | Average delivery time (hours) | Fleet utilization |
|---|---:|---:|---:|
| Normal | 0.20% | 1.16 | 51.5% |
| Surge | 7.04% | 1.81 | 64.8% |
| Typhoon | 39.47% | 3.82 | 80.8% |
| Surge + typhoon | 88.14% | 13.36 | 91.8% |

Combined stress has the largest delay rate and requires 27.4 hours of mean
clearance overtime. Adding a 15% reserve fleet under surge reduces delay from
7.04% to 1.82%: a paired change of **−5.22 percentage points**, with a 95% interval
of **−7.11 to −3.32 points**. Fleet costs are not modeled, so this does not establish
an economically optimal policy. Full intervals, fleet sensitivity and the
[presentation consistency audit](docs/RESULTS.md) accompany the
[generated report](examples/final-run/simulation/REPORT.md).

The **15% ±2 percentage points delay target is hypothetical**. Normal delay lies
outside that band, so the run does not demonstrate target calibration or external
validity. On held-out synthetic demand, statistical WAPE is 9.38% versus 14.95% for
the weekday baseline; nominal 90% intervals cover about 87.0%. These results do
not establish real-world forecast accuracy or delivery benefits. Rare events,
real roads, shifts and independent operational validation remain limitations.

## Submission packaging and reproducibility

```sh
lastmile-submission --results examples/final-run --out outputs/ISE450-simulation.zip
```

The deterministic ZIP includes source, tests, documentation, run inputs/results
and a SHA-256 manifest. Its `project/` directory contains the source and its
`results/` directory contains the selected recorded run. After extracting, install
from `project/`; use `--demand-csv ../results/demand/normal_hourly.csv` to rerun
the packaged inputs into a new output directory. An existing presentation may optionally be included with
`--ppt path/to/presentation.pptx`; no PowerPoint is generated or required to run
the project. Source and tests use an editable installation from the repository.

[Verification evidence](docs/VERIFICATION.md) records test/smoke checks and run
provenance. The [data interface](docs/interface.md) defines CSV schemas and outputs.
Final run manifests and `environment.txt` record settings and dependency versions.
Seeded reproducibility is tested in a fixed runtime; cross-platform floating-point
and compressed model-archive byte identity are not guaranteed. GitHub Actions
runs the tests, simulation smoke checks and ZIP build.
