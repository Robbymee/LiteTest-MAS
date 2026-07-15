from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_m9_1_canary import audit


def test_canary_audit_accepts_two_public_negative_results(tmp_path):
    """验证两项真实 canary 的失败质量结果可以通过公开审计。"""
    rows = [
        {"experiment_group": "S2", "dataset": "mbpp", "task_id": "mbpp_sanitized:591", "result_scope": "m9_1_real_canary", "task_success": False, "public_leakage_count": 0},
        {"experiment_group": "S4", "dataset": "humaneval", "task_id": "humaneval_plus:HumanEval/27", "result_scope": "m9_1_real_canary", "task_success": False, "public_leakage_count": 0},
    ]
    for index, row in enumerate(rows):
        (tmp_path / f"{index}.json").write_text(json.dumps(row), encoding="utf-8")
    result = audit(tmp_path)
    assert result["valid"] is True and result["task_success_count"] == 0


def test_canary_audit_rejects_private_field(tmp_path):
    """验证 canary 公开记录不能包含候选代码字段。"""
    row = {"experiment_group": "S2", "dataset": "mbpp", "task_id": "mbpp_sanitized:591", "result_scope": "m9_1_real_canary", "public_leakage_count": 0, "candidate_code": "blocked"}
    (tmp_path / "bad.json").write_text(json.dumps(row), encoding="utf-8")
    assert audit(tmp_path)["valid"] is False
