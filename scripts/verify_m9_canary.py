from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import PUBLIC_RESULT_REQUIRED, canary_item, task_key

FORBIDDEN = {"candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution", "reference_solution", "official_tests", "contract", "expected_output", "api_key", "authorization"}


def forbidden_keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(forbidden_keys(child) for child in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(forbidden_keys(child) for child in value)) if value else set()
    return set()


def verify(run_root, canary):
    item = canary_item(ROOT, canary)
    key = task_key(item)
    public_path = Path(run_root) / "public" / "tasks" / f"{key}.json"
    attempts = Path(run_root) / "private" / "attempts"
    errors = []
    try:
        record = json.loads(public_path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        return {"valid": False, "errors": ["missing_public_record"], "leakage_count": 0}
    missing = PUBLIC_RESULT_REQUIRED - set(record)
    if missing:
        errors.append("missing_public_schema")
    public_values = []
    for path in (Path(run_root) / "public").rglob("*.json"):
        try:
            public_values.append(json.loads(path.read_text(encoding="utf8")))
        except (OSError, json.JSONDecodeError):
            errors.append("invalid_public_json")
    leakage = sorted(FORBIDDEN & set().union(*(forbidden_keys(value) for value in public_values))) if public_values else []
    if leakage:
        errors.append("forbidden_field")
    if record.get("result_scope") != "m9_runner_canary":
        errors.append("result_scope_mismatch")
    if any(record.get(field) != item[field] for field in ("seed", "experiment_group", "dataset", "task_id", "group_id", "plan_index")):
        errors.append("canary_mapping_mismatch")
    if record.get("parse_status") != "success":
        errors.append("parse_not_success")
    if record.get("official_test_count") is None:
        errors.append("official_metrics_unavailable")
    if record.get("infrastructure_failure") is not False:
        errors.append("infrastructure_failure")
    if not str(record.get("final_status", "")).startswith(("completed_", "failed_")):
        errors.append("non_final")
    files = sorted(attempts.glob(f"{key}-attempt-*.json"))
    if len(files) != record.get("attempt_count"):
        errors.append("attempt_count_mismatch")
    else:
        values = [json.loads(path.read_text(encoding="utf8")) for path in files]
        if [value.get("attempt") for value in values] != list(range(1, len(values) + 1)):
            errors.append("attempt_sequence_mismatch")
        if values and values[-1].get("final_status") != record.get("final_status"):
            errors.append("final_attempt_mismatch")
        if values and any(value.get("task_key") != key or value.get("task_id") != item["task_id"] for value in values):
            errors.append("attempt_identity_mismatch")
    if record.get("resume_count") != max(0, len(files) - 1):
        errors.append("resume_count_mismatch")
    return {"valid": not errors, "errors": errors, "leakage_count": len(leakage), "final_status": record.get("final_status"), "parse_status": record.get("parse_status")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--canary", required=True, choices=["mbpp_g1", "humaneval_g4"])
    args = parser.parse_args()
    result = verify(args.run_root, args.canary)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
