from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import (
    PUBLIC_RESULT_REQUIRED,
    group_config,
    rebuild_inventory,
    select_plan,
    spec_sha256,
    task_identity,
    task_key,
    validate_spec,
    verify_inventory,
)

FORBIDDEN = {"candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution", "reference_solution", "official_tests", "contract", "expected_output", "api_key", "authorization"}


def _read_json(path, errors, label):
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        errors.append(f"invalid_json:{label}")
        return None


def _expected_completion(inventory, spec, freeze_git_sha):
    return {
        "schema_version": "1.0",
        "completion_status": "complete",
        "planned_count": inventory["planned_count"],
        "final_count": inventory["final_count"],
        "inventory_sha256": inventory["inventory_sha256"],
        "spec_sha256": spec_sha256(spec),
        "freeze_git_sha": freeze_git_sha,
        "model": spec["model"],
        "implementation_git_sha": spec["implementation_git_sha"],
        "result_scope": spec["result_scope"],
    }


def verify(run_root, spec, root=ROOT, strict=False, combination=None, expected_freeze_sha=None):
    validate_spec(spec, spec["implementation_git_sha"])
    planned = select_plan(verify_inventory(Path(root), spec), combination)
    public = Path(run_root) / "public"
    errors = []
    rows = []
    for path in sorted((public / "tasks").glob("*.json")):
        row = _read_json(path, errors, path.name)
        if row is not None:
            rows.append((path, row))
    planned_by_identity = {task_identity(item): item for item in planned}
    identities = []
    for path, row in rows:
        missing = PUBLIC_RESULT_REQUIRED - set(row)
        if strict and missing:
            errors.append("missing_public_schema:" + path.name)
        if FORBIDDEN & set(row):
            errors.append("forbidden_field:" + path.name)
        if not str(row.get("final_status", "")).startswith(("completed_", "failed_")):
            errors.append("non_final:" + path.name)
            continue
        try:
            identity = task_identity(row)
        except KeyError:
            errors.append("invalid_identity:" + path.name)
            continue
        identities.append(identity)
        expected = planned_by_identity.get(identity)
        if expected is None:
            errors.append("unexpected_task:" + path.name)
            continue
        if path.stem != task_key(row):
            errors.append("task_file_name_mismatch:" + path.name)
        if any(row.get(field) != expected[field] for field in ("seed", "experiment_group", "dataset", "task_id", "group_id", "plan_index")):
            errors.append("plan_mapping_mismatch:" + path.name)
        if any(row.get(field) != value for field, value in group_config(expected["experiment_group"]).items()):
            errors.append("combination_mode_mismatch:" + path.name)
        if strict and row.get("result_scope") != spec["result_scope"]:
            errors.append("result_scope_mismatch:" + path.name)
        if strict and row.get("spec_sha256") != spec_sha256(spec):
            errors.append("spec_sha_mismatch:" + path.name)
        if strict and row.get("implementation_git_sha") != spec["implementation_git_sha"]:
            errors.append("implementation_sha_mismatch:" + path.name)
        if strict and row.get("model") != spec["model"]:
            errors.append("model_mismatch:" + path.name)
        if strict and row.get("backend") != spec["backend"]:
            errors.append("backend_mismatch:" + path.name)
        if strict and expected_freeze_sha is None:
            errors.append("missing_expected_freeze_sha")
        elif strict and row.get("freeze_git_sha") != expected_freeze_sha:
            errors.append("freeze_sha_mismatch:" + path.name)
    final_keys = [task_key({"seed": identity[0], "experiment_group": identity[1], "dataset": identity[2], "task_id": identity[3]}) for identity in identities]
    duplicates = sorted({key for key in final_keys if final_keys.count(key) > 1})
    if duplicates:
        errors.append("duplicate_tasks")
    if len(rows) != len(planned):
        errors.append("unexpected_final_count")
    expected_inventory = rebuild_inventory(public, planned)
    if expected_inventory["missing_task_keys"]:
        errors.append("missing_tasks")
    if expected_inventory["duplicate_task_keys"]:
        errors.append("duplicate_tasks")
    stored_inventory = _read_json(public / "inventory.json", errors, "inventory.json")
    if stored_inventory != expected_inventory:
        errors.append("inventory_mismatch")
    if combination is None:
        marker = _read_json(public / "completion.json", errors, "completion.json")
        if marker != _expected_completion(expected_inventory, spec, expected_freeze_sha):
            errors.append("completion_marker_mismatch")
    result = {"valid": not errors, "errors": errors, "final_count": len(rows), "planned_count": len(planned), "inventory": expected_inventory}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--combination")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--expected-freeze-sha")
    parser.add_argument("--json-output", action="store_true")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf8"))
    result = verify(args.run_root, spec, strict=args.strict, combination=args.combination, expected_freeze_sha=args.expected_freeze_sha)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
