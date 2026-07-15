from __future__ import annotations

import json
from pathlib import Path

from experiments.m9_1_runner import group_config, metric_defaults, plan, task_key
from experiments.m9_1_verifier import verify, write_completion


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_strict_verifier_accepts_complete_synthetic_public_run(tmp_path):
    """验证 240 条合成公开记录、completion marker 和 S 组配置。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    public = tmp_path / "public" / "tasks"; public.mkdir(parents=True)
    for item in plan(spec):
        row = {"schema_version": "1.0", **item, **group_config(item["experiment_group"]), **metric_defaults(), "result_scope": spec["result_scope"], "freeze_git_sha": "freeze", "implementation_git_sha": spec["implementation_git_sha"], "task_success": False, "final_status": "failed_official_tests"}
        (public / f"{task_key(item)}.json").write_text(json.dumps(row), encoding="utf-8")
    write_completion(tmp_path / "public", spec, "freeze")
    assert verify(tmp_path, spec, "freeze")["valid"] is True


def test_m9_1_verifier_rejects_missing_and_duplicate_records(tmp_path):
    """验证缺失、重复和缺少 completion marker 不能通过。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    public = tmp_path / "public" / "tasks"; public.mkdir(parents=True)
    item = plan(spec)[0]
    row = {"schema_version": "1.0", **item, **group_config(item["experiment_group"]), **metric_defaults(), "result_scope": spec["result_scope"], "freeze_git_sha": "freeze", "implementation_git_sha": spec["implementation_git_sha"], "task_success": False, "final_status": "failed_official_tests"}
    (public / "one.json").write_text(json.dumps(row), encoding="utf-8")
    assert verify(tmp_path, spec, "freeze")["valid"] is False
