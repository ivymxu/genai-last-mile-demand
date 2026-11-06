# ISE450 GenAI demand and last-mile delivery simulation

Reproducible demand inputs for an ISE450 off-campus Hong Kong e-commerce logistics case. This repository implements synthetic history, a weekday baseline, a learned statistical generative demand model, validation, and scenario exports. It now also includes a SimPy parcel/vehicle simulation, scenario experiments, a Streamlit dashboard and reproducible submission packaging. Fuel costs and real road routing are outside the model.

## Run

Use Python 3.11–3.13 (integration tested with 3.12). From this repository directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
lastmile --out artifacts --seed 42 --days 730 --horizon 14 --samples 200
```

Without installation: `PYTHONPATH=src python3 -m lastmile.cli --out artifacts`.
The destination must be empty. Change `--out` for each experiment. `lastmile --help` lists controls. Tests cover reproducibility, scenario effects, leakage, persistence, invalid inputs, and the complete CLI. GitHub Actions repeats tests and a default run.

## Complete project: one command

After installation, run:

```sh
lastmile-project --out artifacts/project --replications 5 --horizon 3
streamlit run src/lastmile/dashboard.py
```

The first command generates AI demand and runs normal, +30% surge, typhoon,
combined surge/typhoon, ±20% fleet and +15% surge reserve experiments. Results,
95% uncertainty intervals and paired differences appear under
`artifacts/project/simulation/`. Use a new empty output directory for each run.
For a stronger final analysis use `--replications 20 --horizon 7`.
Optional neural run: install `pip install -e '.[neural]'` and add `--model cvae`.
To consume existing exports add `--demand-csv path/to/normal_hourly.csv`.

```sh
lastmile-submission --results artifacts/project --out outputs/technical-submission.zip
# Include the team-reviewed slide deck for the final course package:
lastmile-submission --results artifacts/project --ppt team.pptx --out outputs/final-submission.zip
```

See [TEAM_HANDOFF](TEAM_HANDOFF.md) for Natasha, Cherry/Yoyo, analysis and slide
responsibilities, complete assumptions and ready-to-use reporting guidance.
No teammate coding is needed. [Logistics details](docs/logistics.md) describe outputs
and [committed example results](examples/logistics-run/simulation/REPORT.md) show an
actual reproducible synthetic simulation run. The 15% target is hypothetical;
original example findings are not actual observations. Time outputs are **hours**.

## What the models do

1. A seeded synthetic data-generating process produces daily counts for Hong Kong Island, Kowloon, and New Territories. Assumed shares are 22%, 35%, 43%; base total is about 5,000 parcels/day. It includes weekday and annual seasonality, promotion/rain/holiday indicators, Poisson counts, shared autocorrelated shocks and district noise. These are illustrative assumptions, not measurements. Holidays are random illustrative flags, not an official calendar. Rain is binary, not a weather forecast.
2. Baseline: mean training demand for each weekday and district.
3. Learned generator: ridge regression of log(1 + count) on calendar/context features, followed by circular seven-day block resampling of fitted residual vectors. Whole vectors preserve cross-district dependence; blocks approximate short-run serial dependence. Counts are clipped at zero and rounded. The point forecast uses empirical smearing for log retransformation.
4. Future normal, +30% surge, and disruption paths share the same random residuals/context. Disruption means **20% fewer incoming parcels**, not reduced vehicle capacity. These multipliers are user-defined interventions, not effects learned from evidence. The operational suite separately applies capacity/speed disruption to normal or surge arrivals.

The default is an empirical statistical generator. An optional neural conditional VAE is now available via `--model cvae`; it learns daily joint district demand, with an explicitly assumed hourly allocation via `--hourly`. See [technical and teammate handoff](docs/handoff.md) for installation, architecture, limitations and the demand-model handoff. No hourly training observations are available.

Method background: [Hyndman and Athanasopoulos, bootstrapping and bagging](https://otexts.com/fpp3/bootstrap.html) and [distributional forecasts](https://otexts.com/fpp3/prediction-intervals.html). The joint residual vector and seven-day block choices here are project design decisions.

## Validation and example results

The first 80% of dates train the evaluation model; the last 20% remain held out. No random row split. Context is assumed known in advance; results are conditional forecasts. After evaluation, a separate model is refitted on all history for future scenario generation. No test data enter the evaluation fit. Hyperparameters are fixed, not selected on the holdout.

The committed `examples/default-run` uses seed 42, 730 history days, a 14-day horizon, and 200 future paths per scenario. Held-out diagnostics use 500 paths:

| Measure | Weekday baseline | Conditional model |
|---|---:|---:|
| MAE, parcels per district-day | 231.66 | 145.44 |
| RMSE | 285.06 | 192.26 |
| WAPE | 14.95% | 9.38% |

The nominal 90% interval covers 86.99% of held-out district-days: some undercoverage remains. Average width is 549.47 parcels. Generated versus held-out means are 1556.46 versus 1549.75 parcels per district-day. Mean daily totals are 5069.13 normal, 6589.87 surge, and 4055.31 disruption. See `metrics.json` for full diagnostics and `manifest.json` for parameters, versions, and CSV/report hashes. Model NPZ byte hashes are excluded because ZIP metadata can vary; learned arrays and sampled outputs are tested for round-trip equivalence.

These results demonstrate internal consistency under the synthetic assumptions. The generator and model share similar functional structure, making the exercise favorable to the model. They do not establish real-world accuracy, realism, delay reduction, or business benefit. The proposed 15% delay rate is a hypothetical calibration target, not historical observed data or a finding. The teammate sample delay/time/utilization table is illustrative, not simulation findings. Residual stationarity, fixed shares, limited tails, short history, omitted parameter uncertainty, and exogenous-context uncertainty limit generalization.

Before final reporting, repeat across seeds and rolling date cutoffs, inspect district distributions, correlations and lag dependence, vary block length and shocks, and calibrate intervals on a separate validation period. Real deployment requires permissioned company counts, actual promotion/holiday/weather records, and external validation.

## Outputs and team integration

- `history.csv`: synthetic historical observations.
- `normal.csv`, `surge.csv`, `disruption.csv`: full future paths.
- `model.npz`: learned coefficients and residual vectors; load with `DemandModel.load`.
- `metrics.json`, `manifest.json`: evaluation and experiment provenance.

See [simulation interface](docs/interface.md), [course alignment](docs/course-alignment.md), and [publishing steps](docs/publishing.md). Core API lives in `src/lastmile/model.py`. The default runs offline after installing NumPy; the optional CVAE also requires PyTorch. No private data or API keys are needed. Licensing is intentionally left for the project owner to choose before public distribution.
