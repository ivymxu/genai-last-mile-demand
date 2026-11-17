# Verification and reproducibility evidence

## Submission verification — 2026-11-17

The cleanup is based on merged source commit
`78eb1691e8e2a5122477bb6a75e55c618a6cf8fc`. Demand generation, simulation,
experiment policy/configuration code, dashboard code and all existing tests are
unchanged. Packaging only removes the deleted document from its source list and
clarifies that a presentation is optional. Assumptions and small CLI/UI defaults
are unchanged; final parameters are supplied explicitly.

- **Full suite:** `python -m unittest discover -s tests -v` completed with exit
  code 0: **15 tests passed, no skipped neural tests**, in Python 3.13.9 with
  PyTorch 2.9.1. Coverage includes training/persistence, holdout isolation, seeded
  demand, CSV contracts, parcel conservation, analytical travel/service and
  utilization, zero demand, capacity/speed changes, CLI subprocess execution,
  deterministic packaging and Streamlit controls.
- **Final experiment:** `lastmile-project --out examples/final-run --replications
  20 --horizon 7 --seed 42` completed with exit code 0. Manifests confirm the
  statistical model, 730 history days, 20 paths and seven arrival days per path.
  Seven policies produce 140 records, with clearance after the arrival horizon.
- **Data/result audit:** normal hourly inputs contain 10,080 unique cells
  (`20 × 7 × 24 × 3`). All 20 path calendars are contiguous; normal delivered
  counts reconcile to input totals. Rates/utilization are in range. Means and
  95% t intervals are independently recomputed from replication CSVs. Input and
  generated output hashes match both manifests.
- **Independent reproduction:** rerunning all 20 paths with the imported final
  hourly CSV, seed 42 and seven policies produced byte-identical `results.json`,
  `replications.csv`, `summary.csv`, `REPORT.md` and the normal parcel trace.
- **Packaging:** the final ZIP was built twice from identical inputs, with matching
  bytes; its integrity and every member SHA-256 were verified. Removed documents
  and local environment/cache files are absent. `pip check` reports no broken
  requirements. All local Markdown file links resolve.
- **Dashboard:** a fresh AppTest run used the unchanged default controls and seed
  42. Normal, surge, typhoon and combined scenarios completed, producing three
  KPI cards and scenario/district tables/charts. A live Streamlit server's
  `/_stcore/health` endpoint returned `ok`.
- **Presentation:** Canva design `DAHaHnY4Vtk` was read without editing, including
  visual inspection of slides 13–19. Main final numbers and confidence intervals
  match; [Results](RESULTS.md) records interpretation and rounding qualifications.
- **Preservation:** source control comparison confirms existing tests, operational
  and demand code, `examples/default-run` and `examples/logistics-run` are unchanged.
  Earlier local ignored runs and the separately delivered screenshot are retained.

See [final run provenance](../examples/final-run/RUN.json),
[environment versions](../examples/final-run/environment.txt),
[demand manifest](../examples/final-run/demand/manifest.json) and
[simulation manifest](../examples/final-run/simulation/manifest.json). Fixed seeds
support reproducibility in a fixed environment; floating-point identity across
platforms and model NPZ archive byte identity are not guaranteed.

## Earlier demand verification — historical evidence

The original optional-CVAE implementation was checked with Python 3.12.6,
NumPy 2.3.5 and PyTorch 2.9.1 CPU: 10 demand tests passed, including actual training.
A run with seed 42, 730 history days, 150 epochs, 14 future days, 200 paths and
hourly exports completed. On the 146-day synthetic holdout, weekday WAPE was
14.95%, statistical WAPE 9.38%, CVAE WAPE 9.43%, CVAE MAE 146.14 parcels per
district-day, and CVAE nominal 90% coverage 86.53%. These retain the recorded
historical demand diagnostics; they are not a new final CVAE experiment and do
not establish real-world performance or CVAE superiority.

## Earlier logistics verification — 2026-11-06

Verified locally on 2026-11-06 with Python 3.12.6. The exact installed dependency
versions are in `examples/logistics-run/environment.txt` and the run manifests.

- `python -m unittest discover -s tests -v`: **15 tests passed**, including the
  existing neural and statistical tests, analytical logistics checks, capacity,
  conservation, seeded repeatability, import failures, CLI subprocess success,
  deterministic ZIPs and dashboard controls.
- `lastmile-project --out artifacts/verified --replications 5 --horizon 3`:
  completed with exit code 0; committed outputs in `examples/logistics-run`.
- `lastmile-project --model cvae --epochs 20 --out artifacts/neural-integration --replications 2 --horizon 1`:
  completed with exit code 0. This is a neural integration smoke check, not a
  converged final neural experiment or model-quality claim.
- Streamlit started bound to 127.0.0.1; `/_stcore/health` returned `ok`.
  AppTest exercised normal/surge/typhoon comparisons and changed the fleet control.
- `python -m pip check`: no broken requirements.
- Submission ZIP created, opened and checked with `ZipFile.testzip()`.
  Two identical input packages were also tested for byte equality.

The committed five-replication run is an example, not final empirical validation.
Normal mean delay is approximately 0.0063%, outside the hypothetical 13–17% target
band. Typhoon mean delay is approximately 38.19%, combined stress 81.13%; these are
outputs of these particular assumed operations. The similarity of typhoon delay
to a previously supplied illustrative figure is coincidental. Defaults were not
calibrated to measured logistics data. Review REPORT.md and its uncertainty before
using any result in presentation text.

GitHub Actions runs the suite plus demand/neural/operational smoke commands and
uploads a technical submission ZIP. Local completion is distinct from hosted CI
status; consult the branch/PR checks for the latter.
