> Integration update: the operational simulator and dashboard are now implemented. See [TEAM_HANDOFF](../TEAM_HANDOFF.md) and [logistics implementation](logistics.md). Phase-1 scope statements below describe the original demand component.

# Phase-1 technical handoff

## Demand contributor (implemented)

The original weekday baseline and statistical block-residual generator remain.
An optional trainable CPU conditional VAE learns the joint distribution of three
district daily log counts conditioned on weekday, annual seasonality and binary
promotion/rain/holiday. Its encoder observes counts and context; its decoder uses
context plus a four-dimensional Gaussian latent, with Gaussian observation noise.
Training minimizes Gaussian negative log likelihood plus KL to a standard normal
prior. Scaling is fitted on training dates only. Evaluation uses the last 20%
of dates; the production model is separately refitted on all synthetic history.
The CLI reports weekday/statistical diagnostics alongside CVAE diagnostics.
No model is automatically declared superior. Fixed architecture/epochs are not
selected using the test set. NPZ persistence uses numeric arrays, not pickle.

Run from the repository in a virtual environment:

```sh
python -m pip install -e '.[neural]'
python -m unittest discover -s tests -v
lastmile --model statistical --hourly --out artifacts/statistical
lastmile --model cvae --epochs 150 --hourly --out artifacts/cvae
```

Use a fresh empty destination. Defaults: seed 42, 730 history days, 14 future days,
200 paths. `model.npz` is selected-model-specific: load with `DemandModel.load` or
`ConditionalVAE.load` according to manifest.model. Manifest includes seed, epochs,
versions, split, profile assumption and export hashes. Reproducibility is tested
on CPU within a fixed dependency/runtime environment; cross-platform floating
point identity is not guaranteed. Neural dependencies are optional; base tests
skip neural tests when torch is absent. CI installs them to exercise training.

Limitations: entirely synthetic history, assumed intraday profile, no observed
hourly fitting, no learned disruption response, no neural serial latent process,
no rare-event validation, numerical log-count clipping, fixed hyperparameters.
Daily shared latent variables allow district dependence but do not guarantee
realistic correlations. Compare interval coverage, distribution shape, district
correlations and temporal dependence across seeds/rolling splits before preferring
the CVAE. Demand MAE/WAPE and coverage do not validate vehicle operations.

## Natasha — model summary and simulation specification

Own entities: orders, vehicles, districts and time slots. Document order volume,
distance, vehicle capacity and delivery windows. Instantiate orders from hourly
counts; assign to the nearest available vehicle under an explicit availability,
capacity, distance and tie-breaking rule. Delivery time = distance / district
speed + service time; delay occurs after the promised window. Define units and
queue behavior. Keep the agreed simplifications explicit: speed constant within
each district/scenario, no vehicle breakdown, simplified distances without a real
road network. Synthetic GenAI scenarios are assumptions about possible futures,
not evidence that those futures are representative.

Disruption must be modeled downstream through justified reduced vehicle speed
and/or usable capacity (and documented service constraints). The existing
`disruption.csv` multiplier 0.8 only reduces ARRIVAL DEMAND by 20%; it does not
reduce supply, slow vehicles or imply higher delays. For a promotion during a
typhoon, use the +30% `surge.csv` demand path with downstream disruption settings.
If also assuming a -20% arrival effect, explicitly justify the combined multiplier
1.3 × 0.8 = 1.04; do not silently substitute the lower-demand disruption path.

## Cherry / Yoyo — simulation testing and evidence

The proposed normal 15% delay rate is a HYPOTHETICAL CALIBRATION TARGET, not a
historically observed company measurement. A simulated normal rate within
13–17% is only agreement with that assumed target, not external validation.
Calibrate on separate runs and assess using independent seeds; record assumptions.
Run fleet counts at 80%, 100%, 120% of the agreed base fleet (document integer
rounding); hold demand paths fixed for paired comparisons. Test surge + disruption
and zero/very high arrivals, capacities and speed boundaries as appropriate.
Produce replication-level delay rate, mean delivery time (state hours/days) and
vehicle utilization (define denominator and observation period), with uncertainty.
The demand generator produces NONE of those operational metrics.

The supplied 14.8% / 26.5% / 38.2% delays, 2.3 / 3.1 / 4.5 days and 72% / 94% /
98% utilization are illustrative examples, NOT measured findings. Likewise +15%
extra vehicles and contingency routes are candidate policies to test, not proven
recommendations. Replace example tables only with traceable simulator outputs.

## Integration gate

Operations/import owner remains to be assigned. Confirm every unresolved CSV
requirement in interface.md, import a small path, reconcile counts and archive
simulator settings/version, input manifest and experiment seed with results.
Remaining team deliverables: executable simulation, calibration/test evidence,
policy experiments, presentation and findings. Phase 1 does not complete them.

## Executed verification

Local Python 3.12.6, NumPy 2.3.5, PyTorch 2.9.1 CPU: all 10 unit/integration
tests passed, including actual training (no neural skips). A full CLI run with
seed 42, 730 history days, 150 epochs, 14-day horizon, 200 paths and hourly exports
completed. On the 146-day holdout: weekday WAPE 14.95%, statistical WAPE 9.38%,
CVAE WAPE 9.43%; CVAE MAE 146.14 parcels/district-day and 90% interval coverage
86.53%. These are executed synthetic demand diagnostics, not delivery findings.
They do not show an improvement over the statistical default or establish
real-world performance. Coverage below 90% warrants further calibration.
