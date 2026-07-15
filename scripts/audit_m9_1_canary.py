"""审计 M9.1 真实 canary 的公开字段和敏感内容。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN = {"hidden_reference_tests", "candidate_code", "raw_response", "canonical_solution", "official_tests", "expected_output", "api_key", "authorization", "private_traceback"}
EXPECTED = {("S2", "mbpp", "mbpp_sanitized:591"), ("S4", "humaneval", "humaneval_plus:HumanEval/27")}


def recursive_keys(value: Any) -> set[str]:
    """递归收集字段名。"""
    if isinstance(value, dict):
        return set(value) | set().union(*(recursive_keys(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(recursive_keys(child) for child in value))
    return set()


def contains_path_or_secret(value: Any) -> bool:
    """检查公开 JSON 值中是否出现绝对路径或明显凭据。"""
    if isinstance(value, dict):
        return any(contains_path_or_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_path_or_secret(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return "api_key=" in lowered or "c:\\" in lowered or lowered.startswith("/home/") or lowered.startswith("/root/")
    return False


def audit(run_root: Path) -> dict[str, Any]:
    """审计两项真实 canary，保留 task_success 负结果。"""
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(run_root.glob("*.json"))]
    identities = {(row.get("experiment_group"), row.get("dataset"), row.get("task_id")) for row in rows}
    errors: list[str] = []
    if identities != EXPECTED:
        errors.append("canary_identity_mismatch")
    for row in rows:
        if row.get("result_scope") != "m9_1_real_canary":
            errors.append("result_scope_mismatch")
        if recursive_keys(row) & FORBIDDEN:
            errors.append("forbidden_field")
        if contains_path_or_secret(row):
            errors.append("path_or_secret_pattern")
        if row.get("public_leakage_count") != 0:
            errors.append("public_leakage_count")
    return {"valid": not errors and len(rows) == 2, "errors": sorted(set(errors)), "record_count": len(rows), "task_success_count": sum(bool(row.get("task_success")) for row in rows), "infrastructure_failure": "unavailable"}


def main() -> int:
    """运行 canary 审计 CLI。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
