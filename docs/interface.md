# Demand interface for simulation teammates

Each scenario CSV has exactly these columns:

| Column | Type | Meaning |
|---|---|---|
| date | ISO date | Hong Kong local service date |
| district | enum | HK_Island, Kowloon, New_Territories |
| parcels | nonnegative integer | Aggregate arrivals for the district on that date |
| promotion, rain, holiday | 0 or 1 | Assumed exogenous context shared by all districts on a date |
| scenario | string | normal, surge, disruption, or synthetic_history |
| sample_id | integer | Independent Monte Carlo path identifier within a scenario |

The scenario primary key is (scenario, sample_id, date, district). History has sample_id 0. One complete path contains horizon × 3 rows. Select one sample_id per simulation replication; do not sum different sample_ids together. Use matching sample_ids across scenarios for paired comparisons. Aggregate counts are not parcel records and contain no addresses, intraday arrival times, parcel sizes, or promised delivery deadlines.

Teammates must specify the mapping from district counts to parcel entities, intraday arrival distributions, delivery coordinates, service times, time windows, network distances, vehicles, capacities, and routing policy. Preserve each district-day total when expanding counts. Rain may affect travel/service speed in the simulation, but that effect must be separately justified. Demand reduction in the disruption scenario does not imply a capacity reduction.

Suggested simulation outputs: replication-level delayed parcels / total parcels, utilization, lead time, and optional distance/cost. Compare policies under the same demand paths and report uncertainty across replications. Demand alone cannot identify the highest delay risk: vehicle capacity and routing may change the ordering. No routing policy or simulation engine is provided in phase 1.

Programmatic customization: construct daily dictionaries with date and binary promotion/rain/holiday flags; fit DemandModel on an N×3 count matrix in DISTRICTS order; call sample(rows, samples, seed, multiplier, block). Input rows must be chronological, complete, unique dates for model interpretation; the API does not sort or impute them. The CLI always generates a complete daily calendar.

## Optional hourly contract (phase-1 extension)

Use `--hourly` to add `history_hourly.csv`, `normal_hourly.csv`,
`surge_hourly.csv`, and `disruption_hourly.csv`. Existing daily CSV filenames,
columns, and default statistical behavior remain compatible.

Exact hourly header, in order:

```csv
date,hour,district,parcels,promotion,rain,holiday,scenario,sample_id
```

UTF-8 comma-separated text with a header, no index. `hour` is an integer 0–23,
representing the interval [hour:00, next hour:00) on `date` in Asia/Hong_Kong.
All other types/enums match the daily contract above. Primary key:
`(scenario, sample_id, date, hour, district)`. Every path includes all zero-count
hours and all three districts: horizon × 24 × 3 rows. Rows are ordered by sample,
date, hour, district in DISTRICTS order. For every path/date/district, summing the
24 hourly parcel counts exactly recovers the corresponding daily CSV count.

The intraday two-peak profile in `lastmile.hourly.PROFILE` is an illustrative
multinomial allocation, NOT an hourly pattern learned from data. Daily inputs
cannot identify an hourly profile. Both models learn daily district demand;
the CVAE is not an hourly time-series VAE. Hourly allocation uses a separate
seeded random stream. Paired scenario daily draws share random numbers; hourly
allocations preserve totals but are not parcel-level paired arrivals.

### Operations acceptance checklist and unresolved requirements

This is the repository's exact offered CSV contract; no supplied operational-team
specification establishes their importer requirements. Integration is pending
confirmation of: simulator/software and delimiter/encoding support; daily versus
hourly input; accepted district IDs and mapping; local date/hour versus timestamp;
aggregate counts versus one order per row; one path per file versus sample_id;
arrival-within-hour rule; order IDs, coordinates, parcel capacity units and promised
windows if order-level records are required. Do not invent these missing fields or
claim compatibility with an untested simulator. Import one complete sample_id,
check key uniqueness/nonnegative integer counts, and reconcile district-day totals.
The simulator should instantiate `parcels` orders in each hour using its agreed
within-hour arrival rule. Do not sum alternative Monte Carlo paths.
