# Integration verification

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
