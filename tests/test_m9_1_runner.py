from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.m9_1_runner import canary_item, group_config, plan, select_plan


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_runner_uses_s_group_semantics():
    """验证 S1-S4 配置与 M9 G1-G4 不混用。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    assert len(plan(spec)) == 240
    assert group_config("S2")["component"] == "compact_protocol_v2"
    assert group_config("S4")["memory_enabled"] is True
    assert select_plan(spec, "S3:mbpp:42")[0]["experiment_group"] == "S3"
    assert canary_item(spec, "S4", "humaneval")["task_id"] == "humaneval_plus:HumanEval/27"
    with pytest.raises(ValueError):
        group_config("G1")
