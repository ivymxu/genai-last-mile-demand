# Methodology, assumptions and limitations

## Synthetic demand

The case represents Hong Kong e-commerce deliveries in `HK_Island`, `Kowloon`
and `New_Territories`. No observed company data are used. The history generator
assumes a base of approximately 5,000 parcels/day and district shares of 22%, 35%
and 43%. It combines Poisson counts, weekday and annual seasonality, promotion,
rain and holiday flags, a shared autoregressive shock and district noise. Holidays
are illustrative random flags, not an official calendar; rain is not a forecast.

The CLI generates 730 historical days by default. The first 80% (584 days) train
the evaluation model and the last 20% (146 days) are held out chronologically.
Future context is assumed known. Evaluation is followed by a separate fit on all
history for scenario generation. Test observations do not enter the evaluation
fit, and hyperparameters are not selected using the holdout.

The default statistical generator fits ridge regression to `log(1 + count)` using
calendar/context features, then resamples centred joint district residual vectors
in circular seven-day blocks. Vectors preserve cross-district dependence; blocks
approximate short-run serial dependence. Counts are clipped at zero and rounded.
Point forecasts use empirical smearing for retransformation. The comparison
baseline is the training mean for each weekday and district.

The optional CPU conditional VAE learns joint daily district log counts conditioned
on weekday, annual seasonality and binary promotion/rain/holiday context. The
encoder receives counts and context, a 32-unit hidden layer estimates a
four-dimensional Gaussian latent distribution, and a 32-unit decoder receives
latent values and context and returns Gaussian mean/scale parameters. Training
minimizes Gaussian negative log likelihood plus KL divergence to a standard normal
prior, using Adam at learning rate 0.01. Scaling is fitted on training dates only.
Default training uses 150 epochs. Persistence uses numeric NPZ arrays without
pickle. The VAE is an alternative, not the source of the final statistical run;
no superiority over the statistical model is established.

Both generators learn daily demand. Hourly counts use the explicitly assumed
two-peak multinomial profile in `lastmile.hourly.PROFILE`, with a separate seeded
stream and exact district-day total conservation. The profile is not learned from
hourly observations; the VAE is not an hourly time-series model. See the
[CSV interface](interface.md) for schemas, path selection and import validation.

## Discrete-event logistics model

Entities are individual parcels, three district FIFO queues/depots and a shared
fleet. Each parcel has an arrival time, district, synthetic destination and
promised deadline. Vehicles have a position, availability, capacity and busy time.
Units are hours and kilometres; one parcel is one stop and one capacity unit.

1. Expand each hourly count to exactly that many parcels, arriving uniformly
   within the hour with seeded random destinations.
2. A dispatcher checks every 15 minutes. It selects the district whose oldest
   waiting parcel arrived first, then the nearest idle vehicle to that depot.
   Ties follow stable district/vehicle order. A busy fleet leaves parcels queued.
3. Reserve up to the effective batch capacity from the selected FIFO queue.
   The vehicle travels empty to the district depot to load the reserved batch.
   Vehicles can serve any district; a batch never mixes districts.
4. Deliver using nearest-neighbour stops, spending travel time plus service time
   at each stop, then return empty to that district depot. The vehicle becomes
   available again. Dispatch may wait up to the next dispatch check.
5. Stop only after all input arrivals, queued deliveries and vehicle returns are
   complete. The model starts empty, has no warm-up deletion and represents a
   finite delivery campaign rather than a steady-state system.

| Operational assumption | Value |
|---|---|
| Fleet | 48 vehicles, initially round-robin across depots |
| Capacity | 24 parcels per batch |
| Delivery window | 4 hours from each parcel's arrival |
| Stop service time | 3 minutes per parcel |
| Dispatch interval | 15 minutes |
| District speeds | 18 / 22 / 28 km/h: HK Island / Kowloon / NT |
| Depot coordinates | (0, 0), (8, 0), (8, 12) km |
| Destinations | Uniform within ±3 km on each axis around the district depot |
| Distances | Euclidean; destination-district speed also applies to repositioning |
| Availability | Continuous 24/7 operation, including late-night arrivals |
| Other constraints | No loading time, breaks, shifts, breakdowns or time-varying traffic |

These are modeling assumptions, not estimates of a real fleet. Operations use
constant speed within a district/scenario. The dispatcher is a transparent
heuristic, not an optimizer or a representation of a real road/ferry network.

## Experimental design

The final run uses **20 replications, seven arrival days and base seed 42**, with
730 training-history days and the statistical demand generator. CLI smoke/default
runs use smaller settings; only the explicit final command reproduces the final
experiment. Source and result manifests identify the actual settings.

| Policy identifier | Demand | Operational change from normal |
|---|---|---|
| `normal` | Baseline path | None |
| `surge` | Hourly counts ×1.30, rounded | None |
| `typhoon` | Baseline path | Speed ×0.55; batch capacity ×0.70 |
| `surge_typhoon` | Counts ×1.30, rounded | Speed ×0.55; capacity ×0.70 |
| `fleet_minus20` | Baseline path | 38 vehicles after integer rounding |
| `fleet_plus20` | Baseline path | 58 vehicles after integer rounding |
| `surge_fleet_plus15` | Counts ×1.30, rounded | 55 vehicles after integer rounding |

Capacity reductions are floored, minimum one: the default typhoon capacity is
16 parcels/batch. Hourly rounding means realized surge totals are approximately
30% higher; actual parcel counts are recorded. The demand-only `disruption.csv`
retains its separate meaning of 20% fewer arrivals. The operational suite derives
surge from the normal path and does not use that reduced-demand file as typhoon.
Importing an already-surged CSV as the baseline applies the surge factor again.

Replication i selects demand sample i and operational seed `42 + i`. Policies reuse
matching demand paths/seeds. Different surge counts change random-number
consumption, so surge pairing is at path/seed level, not parcel identity. Fleet and
speed changes can alter batching, so effects need not be monotonic on every path.

## Metrics and uncertainty

- **Delay rate:** parcels completed strictly after arrival plus the promised
  window, divided by all delivered parcels.
- **Average delivery time:** mean completion minus arrival, including queue time,
  in hours. Each replication's mean is parcel-weighted within that run.
- **Fleet utilization:** total busy vehicle-hours divided by fleet size times
  `max(arrival horizon, final dispatch check time)`. Busy time includes service,
  loaded travel and empty reposition/return; queue waiting is idle. The final
  check can add up to one dispatch interval.
- **Clearance overtime:** final dispatch check time beyond the arrival horizon,
  floored at zero. Longer clearance changes the utilization denominator.
- Zero-demand paths report zero delay rate, delivery time and utilization.

Across replications, summary means give each replication equal weight. Two-sided
95% Student-t intervals describe uncertainty in replication means and paired
policy differences; they are unbounded and may cross 0/1 for rates. Paired changes
are policy minus normal, except `reserve_difference_vs_surge`, which compares the
reserve fleet with surge. No multiple-comparison correction is applied.
Intervals approximate sampling uncertainty conditional on fixed assumptions;
they exclude model-parameter, structural and future-context uncertainty. Parcels
within a replication are not independent replications. The dashboard shows one
replication and supplies no inferential interval.

The proposed **15% ±2 percentage points delay band is hypothetical**, not measured
historical behavior. A mean-in-band check is recorded but does not establish
external validity. The model has not been tuned to force agreement with this
band. Originally supplied delay/time/utilization tables were illustrative, not
observed company data or final experiment outputs.

## Limitations

Synthetic history may miss rare events and shares structure with the fitted
statistical generator, making internal evaluation favorable. Fixed district
shares, residual stationarity, limited tails, short history and omitted parameter
uncertainty constrain realism. CVAE daily latent values do not model serial latent
processes or guarantee realistic correlations; numerical log-count clipping is a
safeguard, not tail calibration. The nominal 90% demand interval undercovers the
synthetic holdout. Forecast accuracy does not validate delivery operations.

Rectangular districts, straight-line distances and continuous fleet availability
omit closures, traffic, ferries, shifts and breakdowns. No fuel, labor or fleet
cost model is supplied. Contingency routes and real-world savings cannot be
inferred from these experiments. Stress multipliers are assumed interventions,
not learned forecasts of event likelihood. Independent, permissioned order,
travel and delivery records are needed for calibration and external validation
before operational deployment.

## References

[Forecasting: Principles and Practice — bootstrapping](https://otexts.com/fpp3/bootstrap.html)
and [prediction intervals](https://otexts.com/fpp3/prediction-intervals.html) provide
background for residual resampling and probabilistic demand evaluation.
[SimPy process/events documentation](https://simpy.readthedocs.io/en/stable/simpy_intro/basic_concepts.html)
describes the simulation framework. Dispatch rules, geometry and operational
parameters above are project design decisions.
