"""验证 M9.1 Spec 和 fake canary 的公开门槛，不执行模型。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN = {"hidden_reference_tests", "candidate_code", "raw_response", "canonical_solution", "official_tests", "expected_output", "api_key", "authorization"}


def nested_keys(value: Any) -> set[str]:
    """递归收集 JSON 字段名用于公开泄漏检查。"""
    if isinstance(value, dict):
        return set(value) | set().union(*(nested_keys(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(nested_keys(child) for child in value))
    return set()


def validate_spec(spec: dict[str, Any]) -> list[str]:
    """返回 M9.1 Spec 的结构、规模、scope 和泄漏错误。"""
    errors: list[str] = []
    required = {"experiment_id", "result_scope", "conclusion_scope", "implementation_git_sha", "experiment_groups", "task_plan", "task_plan_count", "group_configs", "preflight_gates"}
    errors.extend(f"missing:{key}" for key in sorted(required - set(spec)))
    if spec.get("result_scope") != "supplementary_competition_alignment_ablation":
        errors.append("result_scope")
    if spec.get("conclusion_scope") != "fixed_task_fixed_model_supplementary_analysis":
        errors.append("conclusion_scope")
    if spec.get("experiment_groups") != ["S1", "S2", "S3", "S4"]:
        errors.append("experiment_groups")
    plan = spec.get("task_plan", [])
    if spec.get("task_plan_count") != 240 or len(plan) != 240:
        errors.append("task_plan_count")
    identities = {(item.get("seed"), item.get("experiment_group"), item.get("dataset"), item.get("task_id")) for item in plan}
    if len(identities) != len(plan):
        errors.append("duplicate_task_identity")
    if [item.get("plan_index") for item in plan] != list(range(len(plan))):
        errors.append("plan_index")
    if FORBIDDEN & nested_keys(spec):
        errors.append("public_leakage:" + ",".join(sorted(FORBIDDEN & nested_keys(spec))))
    for gate in ("unit_tests", "windows_full_tests", "openEuler_full_tests", "fake_canary", "two_real_canaries", "public_leakage_zero", "implementation_freeze_sha", "run_on_freeze_sha"):
        if gate not in spec.get("preflight_gates", []):
            errors.append("missing_gate:" + gate)
    return errors


def verify_fake_canary(record: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    """验证 fake canary 只使用公开字段且不冒充正式结果。"""
    errors = validate_spec(spec)
    if record.get("result_scope") != "m9_1_fake_canary":
        errors.append("fake_scope")
    if record.get("experiment_group") not in spec["experiment_groups"]:
        errors.append("fake_group")
    if record.get("final_status") != "completed_success":
        errors.append("fake_status")
    if FORBIDDEN & set(record):
        errors.append("fake_public_leakage")
    return errors


def main() -> int:
    """执行 Spec 或 fake canary 校验。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--fake-record", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    errors = validate_spec(spec)
    if args.fake_record:
        errors.extend(verify_fake_canary(json.loads(args.fake_record.read_text(encoding="utf-8")), spec))
    print(json.dumps({"valid": not errors, "errors": errors, "task_plan_count": spec.get("task_plan_count")}, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
