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
