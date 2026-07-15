"""验证 M9.1 公开聚合只处理合成 public records。"""

from __future__ import annotations

import json
from pathlib import Path

from experiments.m9_1_runner import group_config, metric_defaults, plan, task_key
from experiments.m9_1_verifier import write_completion
from scripts.aggregate_m9_1_results import aggregate


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_public_aggregate_is_deterministic_and_rejects_private_fields(tmp_path):
    """验证聚合严格读取公开记录并输出 S 组和预注册配对比较。"""
    spec_path = ROOT / "experiments/m9_1/spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    run_root = tmp_path / "run"
    tasks = run_root / "public" / "tasks"
    tasks.mkdir(parents=True)
    for index, item in enumerate(plan(spec)):
        row = {"schema_version": "1.0", **item, **group_config(item["experiment_group"]), **metric_defaults(), "result_scope": spec["result_scope"], "freeze_git_sha": "freeze", "implementation_git_sha": spec["implementation_git_sha"], "task_success": item["experiment_group"] in {"S2", "S3"}, "final_status": "completed_success", "parse_status": "success", "official_test_count": 2, "official_test_pass_count": 2, "sandbox_completion_rate": 1.0, "agent_text_characters": index, "total_tokens": index + 1}
        (tasks / f"{task_key(item)}.json").write_text(json.dumps(row), encoding="utf-8")
    write_completion(run_root / "public", spec, "freeze")
    result = aggregate(run_root, spec_path, tmp_path / "aggregate", "freeze")
    assert result["final_record_count"] == 240
    comparisons = json.loads((tmp_path / "aggregate" / "m9_1_paired_comparisons.json").read_text(encoding="utf-8"))
    assert len(comparisons) == 16
    assert {row["treatment_group"] for row in comparisons} == {"S2", "S3", "S4"}
    first = next(tasks.glob("*.json"))
    row = json.loads(first.read_text(encoding="utf-8")); row["candidate_code"] = "forbidden"; first.write_text(json.dumps(row), encoding="utf-8")
    try:
        aggregate(run_root, spec_path, tmp_path / "rejected", "freeze")
    except ValueError as error:
        assert "strict_verifier_failed" in str(error)
    else:
        raise AssertionError("私有字段必须被拒绝")
