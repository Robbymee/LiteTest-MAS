# Security And Data Boundary

## Public Delivery Contract

The delivery surface contains only aggregate-level experiment metadata and metrics. It must never contain hidden reference tests, candidate code, raw responses, canonical solutions, contracts, credentials, authorization headers, request IDs, model snapshot paths, or absolute host paths.

`scripts/build_m10_dashboard.py` rejects forbidden keys in its aggregate input. `scripts/audit_m10_delivery.py` rejects forbidden keys, credential-like text, and Windows or Linux absolute-path patterns in the generated delivery directory.

## Operational Rules

- Keep `.env`, `models/`, `runs/`, logs, and raw datasets untracked.
- Do not disable TLS verification or use insecure HTTP exceptions for public hosting.
- The Dashboard is an offline artifact; do not add analytics, remote fonts, or third-party scripts.
- Treat the frozen formal output as immutable. Rebuild delivery artifacts into a separate directory.
