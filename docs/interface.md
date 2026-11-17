# Data and output interface

## Daily demand CSV

UTF-8 comma-separated text with a header and no index:

```csv
date,district,parcels,promotion,rain,holiday,scenario,sample_id
```

| Column | Type and meaning |
|---|---|
| `date` | ISO local service date in Asia/Hong_Kong |
| `district` | `HK_Island`, `Kowloon`, `New_Territories` |
| `parcels` | Nonnegative integer district-day arrival count |
| `promotion`, `rain`, `holiday` | Binary assumed context, shared by districts on a date |
| `scenario` | Generator label: normal, surge, disruption or synthetic_history |
| `sample_id` | Nonnegative integer Monte Carlo path ID; history uses 0 |

Primary key: `(scenario, sample_id, date, district)`. A path contains
`horizon × 3` rows. Aggregate counts do not contain addresses, parcel sizes,
individual arrival times or promised deadlines.

## Hourly demand CSV

The demand command's `--hourly` option also exports `history_hourly.csv`,
`normal_hourly.csv`, `surge_hourly.csv` and `disruption_hourly.csv`:

```csv
date,hour,district,parcels,promotion,rain,holiday,scenario,sample_id
```

`hour` is an integer 0–23 for the interval [hour:00, next hour:00). Other columns
retain their daily meanings; `parcels` is the district-hour count. Primary key:
`(scenario, sample_id, date, hour, district)`. Paths include every zero-count cell
and all districts: `horizon × 24 × 3` rows, ordered by sample, date, hour, district
in `DISTRICTS` order. Summing 24 hourly counts exactly recovers each daily count.
The allocation profile is assumed, not learned from hourly observations.

## Simulation import and programmatic use

`load_demand(path, sample_id)` selects one complete path. The suite selects sample
IDs `0..replications-1`; alternative paths must not be summed together. The loader
requires one scenario per selected path, known districts, unique keys,
nonnegative integer counts and a contiguous complete calendar including zeros.
It rejects missing/duplicate cells and fractional counts/hours. The generator's
context columns are retained in exports; the logistics importer uses dates,
hours if present, district, parcels, scenario and sample ID.

Daily inputs are expanded with the assumed hourly profile and seed
`sample_id + 7301`. Within-hour arrivals, coordinates and vehicle rules follow the
[methodology](METHODOLOGY.md). Using a pre-surged input as the suite's baseline
applies another 30% intervention in its surge policy. A scenario label does not
automatically change vehicle speed/capacity. No external simulator compatibility
is claimed.

For custom daily demand, construct chronological unique date dictionaries with
binary context and fit `DemandModel` to an `N × 3` count matrix in `DISTRICTS`
order. `sample(rows, samples, seed, multiplier, block)` produces complete demand
paths; it does not sort dates or impute missing values. `simulate` accepts a
`days × 24 × 3` nonnegative integer array and a validated `Config`.

## Project outputs

| Path below the project run directory | Content |
|---|---|
| `demand/history*.csv` | Synthetic history, daily/hourly |
| `demand/normal*.csv`, `surge*.csv`, `disruption*.csv` | Alternative future paths; disruption is demand-only |
| `demand/model.npz` | Fitted selected demand model; load according to `manifest.model` |
| `demand/metrics.json`, `manifest.json` | Holdout diagnostics, parameters, versions and export hashes |
| `simulation/replications.csv` | Counts, fleet/capacity, rates/times, utilization and overtime per run |
| `simulation/summary.csv`, `results.json`, `REPORT.md` | Means, 95% intervals, paired changes and hypothetical target check |
| `simulation/normal_orders_rep0.csv` | Full normal replication-0 parcel audit trace |
| `simulation/manifest.json` | Configurations, path metadata, versions, input and output hashes |

Only normal replication 0 is persisted as a parcel trace by the CLI suite; other
replications retain aggregate metrics. Dashboard downloads can include all parcel
traces from the selected single-run scenarios. Model NPZ byte hashes are omitted
from the demand manifest because archive metadata can vary; array/prediction
round trips are covered by tests. Existing runs are protected against overwrites.
