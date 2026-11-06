# ISE450 team handoff — no teammate coding required

This repository contains demand modeling, a SimPy logistics simulator, experiments,
a Streamlit dashboard, automated tests and a submission packager. All data and
operating defaults are synthetic assumptions. Do not describe them as company data.
The technical owner installs/runs the commands; teammates interpret the generated
report and prepare/review slides. No downstream simulator implementation is needed.

## Technical owner: run and distribute

Use Python 3.11–3.13, create a virtual environment, and install `pip install -e .`.
Run `lastmile-project --out artifacts/final --replications 10 --horizon 7`.
This trains the statistical demand model on 730 synthetic days, exports daily and
hourly paths, runs seven operational policies and writes results. For neural GenAI,
install `pip install -e '.[neural]'` and add `--model cvae --epochs 150`.
The statistical model is the runnable default; do not claim a VAE was used unless
the demand manifest says `cvae`. Both options are offline after installation.

Run `streamlit run src/lastmile/dashboard.py` for the interactive demonstration.
Send teammates `simulation/REPORT.md`, `summary.csv`, `results.json`, and screenshots
from a completed dashboard run. Dashboard runs are single replications; final
comparisons must use the multiple-replication CLI report. To reuse existing demand:
`lastmile-project --demand-csv path/to/normal_hourly.csv --replications 5 --out artifacts/imported`.
IDs 0 through 4 must exist in that file. Daily CSVs are also accepted and expanded
with the documented assumed profile. Never sum alternative sample IDs together.

## Natasha — model summary / section 5

Entities: individual parcel orders, one shared vehicle fleet, three districts,
district depots, hourly demand cells and district FIFO waiting queues. Attributes:
arrival timestamp, district, synthetic delivery coordinate, delivery deadline,
vehicle position, parcel capacity and busy time. Unit: kilometres and hours.

Flow: daily AI-generated counts → seeded hourly allocation → uniform arrival within
each hour → create exactly that many parcels → district FIFO queue → periodic
15-minute dispatcher → oldest waiting district first → nearest idle vehicle to that
district's depot → load up to capacity → nearest-neighbour deliveries → return to
the depot. Completion includes travel plus service time; delay means completion
strictly later than arrival + delivery window. A busy fleet leaves parcels queued.
Vehicles can serve any district but batches never mix districts. A vehicle reserves
its batch when dispatched, then repositions to load at that district depot.

Default assumptions (not estimates): 48 vehicles, 24 parcels per batch, 4-hour
window, 3 minutes per stop; district speeds 18/22/28 km/h for HK Island/Kowloon/New
Territories. Depot coordinates are (0,0), (8,0), (8,12); customers are uniform within
±3 km on each axis around their depot. Euclidean distances replace roads/ferries.
No loading time, breaks, breakdowns, shifts, traffic variation or vehicle sharing
with other work. One parcel is one stop and capacity unit. Operations run 24/7;
late-night arrivals are allowed by the inherited hourly profile. Vehicles are
initially spread round-robin across depots. Empty repositioning and depot return
consume time. Dispatch waits at most one dispatch interval after a vehicle frees.

The run starts empty, accepts arrivals for the specified number of days, then
continues until every parcel is delivered and every vehicle returns. There is no
warm-up removal: this is a finite campaign experiment, not a stationary system.
Fleet utilization = busy vehicle hours / (fleet × max(input horizon, final dispatch
check time)). The final check can add at most one dispatch interval. Busy time
includes service, loaded travel and empty reposition/return; waiting is idle.
Average delivery time is parcel-weighted within each replication, in hours (not
days), including queue time. Zero-demand paths report zero rate/time/utilization.

Limitations: synthetic demand may miss black swans; district rectangles and roads
are simplified; the dispatcher is a transparent heuristic, not an optimizer;
continuous availability can understate shift-related delays. Scenario assumptions
are plausible stress tests, not evidence of future likelihood. Capacity and speed
must be checked against real operations before real decisions.

## Cherry / Yoyo — model testing / section 6

1. Run `python -m unittest discover -s tests -v`. Tests cover inherited demand and
   neural exports, parcel conservation, seeded repeatability, an analytically
   computed one-parcel travel/service/utilization case, zero demand, capacity
   reduction, severe slowdown, importer failures, end-to-end suite/ZIP and dashboard
   control changes. GitHub Actions repeats these and both demand model smoke runs.
2. Read the normal delay estimate and its 95% Student-t interval in REPORT.md.
   The proposed **15% ±2 percentage points is a hypothetical calibration target**.
   `results.json` records a mean-in-band check; it is not a real-world validation
   pass. We do not tune the model to produce 14.8% or any other supplied example.
   Actual validation requires independent permissioned measured delivery records.
3. Inspect `fleet_minus20` and `fleet_plus20`. Fleet sizes are rounded to whole
   vehicles and reported explicitly. Compare paired delay/time/utilization changes
   in `results.json`; direction need not be monotonic for every random path because
   fleet changes also change dispatch/batching. Do not assert a benefit without
   checking the interval and operational trade-off.
4. Inspect `surge_typhoon` for a promotion during typhoon conditions. Normal arrivals
   are multiplied by 1.3, speed by .55, and capacity by .70 (floor, minimum one).
   `typhoon` changes operations only. The original demand `disruption.csv` means
   fewer arrivals and is preserved; it is not silently used as a typhoon path.
5. Replication i uses demand sample i and operational seed base+i. The same demand
   path/seed is reused for fleet and typhoon comparisons. Surge rounds each hourly
   cell ×1.3, so the total increase is approximately 30%; actual totals are reported.
   Different counts alter random-number consumption, so surge is paired at the
   path/seed level, not the identity of each parcel. Sample-path variation and
   arrival/location randomness contribute to uncertainty; model parameter and
   structural uncertainty are excluded. More independent replications improve
   precision; do not treat parcels within one run as independent replications.
6. Summary means give each replication equal weight. Intervals are two-sided 95%
   Student-t intervals on replication means/differences and are unbounded (may cross
   0/1 for rates). They are approximate for small/skewed samples; use 20–30+
   replications for stronger inference. No multiple-comparison correction is used.
   A 2-replication smoke test is not suitable evidence for final findings.

## Analysis members — section 7

Use the generated table, not the originally supplied 14.8%/26.5%/38.2% figures or
2.3/3.1/4.5 days. Those were illustrative examples, not observed or modeled results.
Report the run seed, horizon, fleet, replication count, units and assumptions next
to every chart. Explain both queue congestion and utilization; utilization is
averaged over the full clearance horizon and can fall despite severe delay when
clearance grows. Inspect overtime and district results in the parcel trace.

`surge_fleet_plus15` tests the proposed 15% reserve against surge. Use `reserve_difference_vs_surge` in `results.json` for its paired difference
from surge, and inspect the raw replications.
Do not automatically recommend it: describe benefit, remaining delay, fleet cost
(not modeled), and uncertainty. Route contingencies remain a qualitative proposal;
this model does not represent real road closures or alternate road networks.

## Presentation members — submission checklist

Suggested slides: problem and synthetic-data disclosure; demand model/CVAE choice;
process flow and entity/attribute table; assumptions; analytical/software checks;
normal target comparison with careful wording; surge/typhoon table and uncertainty;
fleet sensitivity and reserve policy; limitations and conditional recommendations;
dashboard demonstration; reproducibility and repository link.

The technical project is complete; the team must review course-specific slide
content and add names/student IDs. A PPT is not automatically fabricated by the
packager. Export the team-reviewed slides as `team.pptx`, then run:

```
lastmile-submission --results artifacts/final --ppt team.pptx --out outputs/ISE450-submission.zip
```

This includes the PPTX, Python simulation/demand/dashboard source, tests, docs,
input/output files and hashes. Without `--ppt`, it produces a technical-only ZIP
clearly marked as such. The build command satisfies reproducible packaging; check
your instructor's required filename, file size and whether separate PPT/simulation
uploads are required. Unzip and follow the included README on a clean machine.
No environment folders, credentials or unrelated files are packaged. Generated ZIP
entries have fixed timestamps, so identical inputs yield identical ZIP bytes.
