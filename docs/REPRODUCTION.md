# Reproduction

## Preconditions

- openEuler 24.03-LTS-SP3 x86_64 with Python 3.
- A fresh clone of the delivery revision.
- Locally available processed task data only for strict plan reconstruction; no model download is required.
- The immutable M9 formal run root and its public aggregate directory.

## Procedure

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest tests/
python3 scripts/aggregate_m9_results.py \
  --run-root <formal-run-root> \
  --spec experiments/m9_experiment_spec.json \
  --plan-root <frozen-plan-checkout> \
  --output-dir <aggregate-output-dir> \
  --expected-freeze-sha cc7aac0417afb6acab47baaf7449459692fa9444
python3 scripts/build_m10_dashboard.py \
  --aggregate-dir <aggregate-output-dir> \
  --output-dir <dashboard-output-dir>
python3 scripts/audit_m10_delivery.py --delivery-dir <dashboard-output-dir>
git diff --check
```

Record the formal freeze SHA, Spec SHA, aggregate input checksum, aggregate checksum, Dashboard checksums, and actual command output. Do not substitute a Windows result for the openEuler validation.
