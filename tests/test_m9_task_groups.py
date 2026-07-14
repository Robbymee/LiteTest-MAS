from __future__ import annotations

import json
from pathlib import Path

from scripts.analyze_m9_task_groups import build_report, read_csv, unique_task_plan


ROOT = Path(__file__).resolve().parents[1]


def test_task_plan_uses_real_manifest_groups_and_ids():
    """确认任务组和任务 ID 来自正式 manifest，而非报告脚本手工命名。"""
    spec = json.loads((ROOT / "experiments/m9_experiment_spec.json").read_text(encoding="utf-8"))
    plan = unique_task_plan(spec)
    assert set(plan) == {
        ("mbpp", "mbpp_list_rearrangement"),
        ("mbpp", "mbpp_regex_string_matching"),
        ("humaneval", "humaneval_string_transforms"),
        ("humaneval", "humaneval_list_transforms"),
    }
    assert plan[("mbpp", "mbpp_list_rearrangement")] == [
        "mbpp_sanitized:591", "mbpp_sanitized:644", "mbpp_sanitized:586", "mbpp_sanitized:743", "mbpp_sanitized:632"
    ]
    assert all(len(task_ids) == 5 for task_ids in plan.values())


def test_report_contains_dataset_metrics_and_public_memory_boundary():
    """确认报告覆盖两类数据集、G1-G4 和 Memory 字段边界。"""
    spec = json.loads((ROOT / "experiments/m9_experiment_spec.json").read_text(encoding="utf-8"))
    dataset_rows = read_csv(ROOT / "reports/m9/dataset_group_summary.csv")
    memory_rows = read_csv(ROOT / "reports/m9/memory_reuse_detail.csv")
    report = build_report(spec, dataset_rows, memory_rows)
    assert "| mbpp | G1 |" in report
    assert "| humaneval | G4 |" in report
    assert "mbpp_sanitized:591" in report
    assert "humaneval_plus:HumanEval/149" in report
    assert "accept、reject、abstain、注入 Token 和 effective reuse 未在公开字段中记录" in report
    assert "hidden tests" in report
