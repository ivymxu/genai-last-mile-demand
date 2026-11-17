# Final results and presentation consistency

## Recorded experiment

The final experiment is [examples/final-run](../examples/final-run), generated on
2026-11-17 from the simulator and assumptions in source commit
`78eb1691e8e2a5122477bb6a75e55c618a6cf8fc`. It is a new run; the existing
[5-replication, 3-day example](../examples/logistics-run/simulation/REPORT.md) and
[14-day, 200-path demand example](../examples/default-run/manifest.json) remain
unchanged. No older outputs are relabeled as final.

```sh
lastmile-project --out examples/final-run --replications 20 --horizon 7 --seed 42
```

This is the original recorded command. The directory is now populated: use a new
empty `--out` directory to reproduce it. The generator is statistical, with 730
synthetic historical days and future sample IDs 0–19. Each replication has seven
arrival days. Operations start with 48 vehicles, 24 parcels/batch, a four-hour
window, three-minute service time and the original geometry/speeds. Seven policies
produce 140 replication records. Clearance continues beyond the seven days.

The [demand manifest](../examples/final-run/demand/manifest.json) and
[simulation manifest](../examples/final-run/simulation/manifest.json) identify
settings, versions and hashes. The [generated report](../examples/final-run/simulation/REPORT.md),
[replication CSV](../examples/final-run/simulation/replications.csv) and
[full results](../examples/final-run/simulation/results.json) are the evidence.

## Operational results

| Scenario | Mean delay % (95% t interval) | Mean delivery hours | Utilization % |
|---|---:|---:|---:|
| Normal | 0.20 (−0.03, 0.43) | 1.16 | 51.5 |
| Surge +30% | 7.04 (4.53, 9.54) | 1.81 | 64.8 |
| Typhoon | 39.47 (33.48, 45.46) | 3.82 | 80.8 |
| Surge + typhoon | 88.14 (83.98, 92.30) | 13.36 | 91.8 |
| Fleet −20%: 38 vehicles | 5.72 (3.65, 7.80) | 1.70 | 64.8 |
| Fleet +20%: 58 vehicles | 0.00 (−0.00, 0.00) | 1.07 | 42.5 |
| Surge +15% reserve: 55 vehicles | 1.82 (0.86, 2.78) | 1.39 | 56.8 |

Values are equal-weight means across 20 independent replications. Displayed zeros
are rounded: fleet +20% mean delay is approximately 0.000814%, not exactly zero.
Student-t intervals are not clipped to the feasible rate bounds. They describe
conditional replication uncertainty, not uncertainty over model assumptions.

The reserve policy is compared with **surge**, not normal. Its paired change is
−5.22 percentage points (95% CI −7.11 to −3.32). Mean delivery time changes by
−0.424 hours (95% CI −0.496 to −0.352). Combined stress has mean clearance
overtime 27.4125 hours. Costs are not modeled, and no real-world savings or optimal
fleet policy is established.

Normal mean delay is about 0.199% and is outside the hypothetical 13–17% band.
This is not evidence of calibration against a real historical delay rate. The
15% value and the originally supplied sample operational table are assumptions
and illustrations, not measured observations.

## Demand diagnostics

On 146 held-out synthetic dates, the weekday baseline has MAE 231.66 parcels per
district-day, RMSE 285.06 and WAPE 14.95%. The statistical generator has MAE 145.44,
RMSE 192.26 and WAPE 9.38%. Nominal 90% intervals cover approximately 86.99% of
held-out district-days. Context is assumed known; the generator shares structure
with the synthetic history process. These are internal demand diagnostics, not
logistics validation or proof of CVAE superiority.

## Presentation audit — 2026-11-17

Source: Canva design `DAHaHnY4Vtk`, **ISE450 Group Project**, 26 slides. The design
was inspected read-only, including text/notes and visual previews of slides 13–19.
The audit applies to that snapshot; the deck was not edited.

| Presentation item | Repository comparison |
|---|---|
| Slide 5–8 architecture, 730 history days, 584/146 split, default statistical model | Matches source and demand manifest; the displayed MAE/WAPE/coverage values match after rounding |
| Slides 9–11 dispatch and operational defaults | Matches simulator assumptions; audit-trace qualification below applies |
| Slides 14–15 seven-scenario table, delay intervals, hours and utilization | Matches the new final run to displayed precision |
| Slide 16 combined delay 88.14% and utilization 91.8% | Matches |
| Slide 17: 20 replications, 7 days, seed 42, baseline fleet and policy deltas | Matches, including all displayed differences versus normal |
| Slide 17 reserve versus surge: 7.04% → 1.82%, −5.22 pp, CI −7.11 to −3.32 | Matches `reserve_difference_vs_surge` |
| Slide 18 plotted delay/utilization points | Match the scenario means at displayed precision |
| Slide 19: surge 7.04%, typhoon 39.47%, combined 88.14%, overtime 27.4 h | Matches |
| Slide 19 additive reference 46.51% and approximately 1.9× ratio | 46.51% sums the two displayed rounded rates. The unrounded sum is 46.5041%; the baseline-adjusted additive prediction is 46.31%. All give about 1.9× but use different definitions |

### Qualifications affecting interpretation

- Slide 17's phrase “the only effect whose CI excludes zero” is too broad.
  Delay-rate changes for surge, typhoon, combined stress and fleet −20% versus
  normal also exclude zero. Among the tested **delay-reducing fleet policies**,
  reserve versus surge excludes zero, whereas fleet +20% versus normal does not.
  The comparison and metric need to be specified; no multiplicity adjustment is used.
- Slide 19's baseline-adjusted additive calculation is
  `surge + typhoon − normal = 46.3051%`; combined delay divided by this is about
  1.9035. The chart's 46.51% instead adds the rounded 7.04% and 39.47%. The unrounded
  sum is 46.5041% (46.50% at two decimals). This is a point-estimate comparison, not a
  separately tested statistical interaction or proof about actual disasters.
- Slide 18's “48 vans” caption is the baseline, not every plotted policy: the
  fleet variants have 38, 58 and 55 vehicles. Its 60% utilization trigger is a
  heuristic annotation, not a threshold estimated or validated by this model.
- Verification tests support specified behaviors; slide 13's wording does not
  establish that no coding errors exist. Slide 14's favorable-assumption
  explanation does not establish empirical validity of the 15% target comparison.
- Slide 16's “system breakdown” should be read as severe simulated congestion.
  No vehicle failures are modeled; the experiment still clears all queues.
- Slide 11 notes imply every reported number has a persisted stop record. The CLI
  persists parcel traces only for **normal replication 0**, plus aggregates for
  every run. The dashboard can export traces for its selected single-run scenarios.

The numerical results agree with the presentation after rounding, subject to the
additive-definition qualification. Interpretive claims require the qualifications
above; neither the model nor the presentation has been altered to force agreement.
