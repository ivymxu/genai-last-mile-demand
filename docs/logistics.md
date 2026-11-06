# Logistics implementation and outputs

The source of truth for model assumptions, member responsibilities and reporting
language is [TEAM_HANDOFF](../TEAM_HANDOFF.md). `lastmile-project --help` lists
operational controls. Existing `lastmile` commands and CSV exports are unchanged.

- `simulation.py`: strict daily/hourly path reader and finite-horizon SimPy events.
- `experiments.py`: seven scenarios, seeded replications, Student-t intervals,
  paired differences, manifests and reports.
- `dashboard.py`: controls, optional CSV upload, scenario charts, district and
  time-of-arrival summaries and downloadable metrics/traces.
- `submission.py`: deterministic source/results ZIP with optional supplied PPTX.

Input must contain complete unique district-day cells (daily) or district-hour-day
cells (hourly), including zeros and contiguous dates. One scenario per CSV is
required. An explicit sample ID selects one path. The loader rejects fractional
counts/hours, negatives, unknown districts, duplicates and missing cells. Daily
inputs use the inherited hourly profile with seed sample_id+7301. A date is a local
service date; no daylight-saving conversion is performed for Hong Kong.

The operational experiment suite deliberately derives surge from normal counts,
so speed/capacity/fleet effects have a common baseline. Existing demand exports
remain available in `demand/`, including their separate demand-only disruption.
Import a generated surge file as a baseline only if you intend the suite to apply
another 30% multiplier; filename labels do not override operational controls.

Outputs under the selected project folder:

- `demand/`: generator model, normal/surge/disruption daily/hourly inputs and validation.
- `simulation/replications.csv`: actual fleet/capacity, counts, delay, delivery time,
  utilization, observation duration and clearance overtime per scenario/run.
- `summary.csv`, `results.json`, `REPORT.md`: replication statistics, 95% intervals,
  paired normal-baseline differences and hypothetical target check.
- `normal_orders_rep0.csv`: every normal replication-0 parcel with arrival,
  completion, district, vehicle and delay for audit and supplementary charts.
- `manifest.json`: complete policy configs, input hash, sample metadata, versions
  and output hashes. Demand provenance has its own manifest.

Reproduce with the recorded command parameters, dependency versions and input hash.
For exact environment capture, save `python -m pip freeze > environment.txt` alongside
the run. No real-world operating dataset or road network is bundled.

Design references: [SimPy process/events documentation](https://simpy.readthedocs.io/en/stable/simpy_intro/basic_concepts.html)
and [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
The operations assumptions and dispatcher are project decisions, not prescriptions
from those libraries.
