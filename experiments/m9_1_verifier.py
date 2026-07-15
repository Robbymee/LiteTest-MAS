"""M9.1 S1-S4 公开结果的独立 Strict Verifier。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.m9_1_runner import METRIC_FIELDS, group_config, plan, task_key

FORBIDDEN = {"candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution", "official_tests", "expected_output", "api_key", "authorization", "private_traceback"}
REQUIRED = {"schema_version", "seed", "experiment_group", "dataset", "group_id", "task_id", "plan_index", "mode", "state_enabled", "memory_enabled", "component", "result_scope", "freeze_git_sha", "implementation_git_sha", "task_success", "final_status", *METRIC_FIELDS}


def spec_hash(spec: dict[str, Any]) -> str:
    """计算不含自引用字段的稳定 Spec 摘要。"""
    return hashlib.sha256(json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def inventory(rows: list[dict[str, Any]], planned: list[dict[str, Any]]) -> dict[str, Any]:
    """构建公共 inventory，记录缺失和重复而不包含私有内容。"""
    expected = [task_key(item) for item in planned]
    actual = [task_key(row) for row in rows]
    return {"planned_count": len(planned), "final_count": len(rows), "missing_task_keys": [key for key in expected if key not in actual], "duplicate_task_keys": sorted({key for key in actual if actual.count(key) > 1})}


def verify(run_root: Path, spec: dict[str, Any], freeze_git_sha: str) -> dict[str, Any]:
    """验证完整 240 条公开结果和 completion marker。"""
    public = run_root / "public"
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((public / "tasks").glob("*.json"))]
    planned = plan(spec)
    expected = {(item["seed"], item["experiment_group"], item["dataset"], item["task_id"]): item for item in planned}
    errors: list[str] = []
    for row in rows:
        identity = (row.get("seed"), row.get("experiment_group"), row.get("dataset"), row.get("task_id"))
        item = expected.get(identity)
        if not item:
            errors.append("unexpected_task")
            continue
        if REQUIRED - set(row): errors.append("missing_public_schema")
        if FORBIDDEN & set(row): errors.append("forbidden_field")
        if any(row.get(key) != item[key] for key in ("seed", "experiment_group", "dataset", "group_id", "task_id", "plan_index")): errors.append("plan_mapping_mismatch")
        if any(row.get(key) != value for key, value in group_config(item["experiment_group"]).items()): errors.append("group_config_mismatch")
        if row.get("result_scope") != spec["result_scope"] or row.get("freeze_git_sha") != freeze_git_sha or row.get("implementation_git_sha") != spec["implementation_git_sha"]: errors.append("metadata_mismatch")
        if not str(row.get("final_status", "")).startswith(("completed_", "failed_")): errors.append("non_final")
    inv = inventory(rows, planned)
    if inv["missing_task_keys"]: errors.append("missing_tasks")
    if inv["duplicate_task_keys"]: errors.append("duplicate_tasks")
    marker_path = public / "completion.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8")) if marker_path.exists() else None
    expected_marker = {"completion_status": "complete", "planned_count": 240, "final_count": 240, "freeze_git_sha": freeze_git_sha, "spec_sha256": spec_hash(spec), "result_scope": spec["result_scope"]}
    if marker != expected_marker: errors.append("completion_marker_mismatch")
    return {"valid": not errors, "errors": sorted(set(errors)), "inventory": inv}


def write_completion(public: Path, spec: dict[str, Any], freeze_git_sha: str) -> None:
    """在完整 public/tasks 已写入后创建独立 completion marker。"""
    marker = {"completion_status": "complete", "planned_count": 240, "final_count": 240, "freeze_git_sha": freeze_git_sha, "spec_sha256": spec_hash(spec), "result_scope": spec["result_scope"]}
    (public / "completion.json").write_text(json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
