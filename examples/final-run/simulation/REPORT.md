# Synthetic logistics experiment results

All values are model outputs under assumed operations, not historical measurements.

| Scenario | Delay rate (95% t CI) | Mean delivery hours | Utilization |
|---|---:|---:|---:|
| normal | 0.20% (-0.03%, 0.43%) | 1.16 | 51.5% |
| surge | 7.04% (4.53%, 9.54%) | 1.81 | 64.8% |
| typhoon | 39.47% (33.48%, 45.46%) | 3.82 | 80.8% |
| surge_typhoon | 88.14% (83.98%, 92.30%) | 13.36 | 91.8% |
| fleet_minus20 | 5.72% (3.65%, 7.80%) | 1.70 | 64.8% |
| fleet_plus20 | 0.00% (-0.00%, 0.00%) | 1.07 | 42.5% |
| surge_fleet_plus15 | 1.82% (0.86%, 2.78%) | 1.39 | 56.8% |

Intervals describe replication uncertainty conditional on fixed assumptions. See results.json for paired differences.
15% ±2 percentage points is a hypothetical calibration band, not measured history. No parameters are fitted to force that result.

Normal mean within hypothetical 13–17% band: False. A mismatch requires investigating assumptions, not claiming validation.
