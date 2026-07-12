# Deployment

## Supported Delivery

The M10 delivery is a static offline Dashboard. It needs only a browser after generation and makes no network request, model request, or private-test request.

Build it from the public M9 aggregate:

```bash
python3 scripts/build_m10_dashboard.py \
  --aggregate-dir <public-aggregate-dir> \
  --output-dir <delivery-dir>
python3 scripts/audit_m10_delivery.py --delivery-dir <delivery-dir>
```

Open `<delivery-dir>/index.html` directly in a browser. The page embeds its sanitized data so it also works when opened from the filesystem rather than a web server.

## Runtime Boundaries

- Dashboard input is limited to aggregate manifest, group, dataset, seed, and paired-comparison JSON.
- Task records, private attempts, raw model responses, candidate code, official tests, credentials, and model snapshots are excluded.
- Core M10 scripts use the Python standard library; no new package is required.
