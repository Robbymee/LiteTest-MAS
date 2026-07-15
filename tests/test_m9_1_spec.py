from __future__ import annotations

import json
from pathlib import Path

from scripts.build_m9_1_spec import build_spec


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_spec_is_independent_and_maps_all_240_public_tasks():
    """验证 M9.1 使用真实 M9 task ID，但拥有独立 scope 和 S1-S4。"""
    m9 = json.loads((ROOT / "experiments/m9_experiment_spec.json").read_text(encoding="utf-8"))
    spec = build_spec(m9, "implementation-sha")
    assert spec["result_scope"] == "supplementary_competition_alignment_ablation"
    assert spec["conclusion_scope"] == "fixed_task_fixed_model_supplementary_analysis"
    assert spec["experiment_groups"] == ["S1", "S2", "S3", "S4"]
    assert spec["task_plan_count"] == 240
    assert len({(x["seed"], x["experiment_group"], x["dataset"], x["task_id"]) for x in spec["task_plan"]}) == 240
    assert all(x["experiment_group"] in {"S1", "S2", "S3", "S4"} for x in spec["task_plan"])
    assert not {"hidden_reference_tests", "canonical_solution", "official_tests"} & set(json.dumps(spec))


def test_m9_1_spec_keeps_formal_parameters_and_v2_components():
    """验证模型、数据集、seed、生成参数和 V2 组件声明未被调优改变。"""
    m9 = json.loads((ROOT / "experiments/m9_experiment_spec.json").read_text(encoding="utf-8"))
    spec = build_spec(m9, "sha")
    assert spec["model"] == m9["model"] and spec["datasets"] == m9["datasets"] and spec["seeds"] == m9["seeds"]
    assert spec["generation_parameters"] == m9["generation_parameters"]
    assert spec["component_versions"]["protocol"] == "compact_protocol_v2"
    assert spec["component_versions"]["state_vector"] == "state_vector_v2"
    assert spec["component_versions"]["shared_memory"] == "gated_shared_memory_v2"
