# Synthetic logistics experiment results

All values are model outputs under assumed operations, not historical measurements.

| Scenario | Delay rate (95% t CI) | Mean delivery hours | Utilization |
|---|---:|---:|---:|
| normal | 0.01% (-0.01%, 0.02%) | 1.12 | 51.6% |
| surge | 3.26% (-2.74%, 9.25%) | 1.69 | 64.7% |
| typhoon | 38.19% (26.48%, 49.89%) | 3.52 | 78.2% |
| surge_typhoon | 81.13% (67.73%, 94.53%) | 8.84 | 87.5% |
| fleet_minus20 | 2.53% (-2.28%, 7.35%) | 1.62 | 64.9% |
| fleet_plus20 | 0.00% (0.00%, 0.00%) | 1.06 | 42.4% |
| surge_fleet_plus15 | 0.25% (-0.42%, 0.92%) | 1.29 | 56.9% |

Intervals describe replication uncertainty conditional on fixed assumptions. See results.json for paired differences.
15% ±2 percentage points is a hypothetical calibration band, not measured history. No parameters are fitted to force that result.

Normal mean within hypothetical 13–17% band: False. A mismatch requires investigating assumptions, not claiming validation.
