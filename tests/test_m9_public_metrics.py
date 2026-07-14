from __future__ import annotations

from scripts.analyze_m9_public_metrics import UNAVAILABLE, analyze_records, write_csv, write_report


def record(group: str, *, dataset: str = "mbpp", seed: int = 42, index: int = 0) -> dict:
    """构造只包含公共字段的合成 M9 记录，避免测试依赖私有工件。"""
    return {
        "experiment_group": group, "dataset": dataset, "seed": seed, "group_id": "group_1", "task_id": f"task-{group}-{index}", "plan_index": index,
        "message_count": 5, "text_character_count": 100, "prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30,
        "request_count": 1, "latency_seconds": 1.5, "state_vector_count": int(group in {"G3", "G4"}), "state_vector_bytes": 64 if group in {"G3", "G4"} else 0,
        "memory_reference_ids": ["m0001"] if group == "G4" else [], "memory_read_count": 2 if group == "G4" else 0,
        "memory_hit_count": 1 if group == "G4" else 0, "memory_reuse_count": 1 if group == "G4" else 0, "memory_write_count": 1 if group == "G4" else 0,
        "official_test_count": 2, "official_test_pass_count": 2, "parse_status": "success", "sandbox_completed": True,
        "task_success": True, "infrastructure_failure": False, "model_quality_failure": False,
    }


def test_public_metrics_keep_missing_communication_state_and_memory_fields_unavailable():
    """验证缺失的分层字段不会被聚合器伪造成零值。"""
    artifacts = analyze_records([record("G1"), record("G4", index=1)])
    communication = next(row for row in artifacts["communication_layer_summary"] if row["experiment_group"] == "G1")
    state = next(row for row in artifacts["state_efficiency_summary"] if row["experiment_group"] == "G4")
    memory = artifacts["memory_reuse_detail"][0]

    # 这些字段没有出现在 M9 公共 schema 中，必须明确保留 unavailable。
    assert communication["agent_text_tokens"] == UNAVAILABLE
    assert communication["protocol_payload_bytes"] == UNAVAILABLE
    assert state["equivalent_text_state_bytes"] == UNAVAILABLE
    assert state["state_compression_ratio"] == UNAVAILABLE
    assert memory["memory_accept_count"] == UNAVAILABLE
    assert memory["memory_effective_reuse_rate"] == UNAVAILABLE


def test_public_metrics_only_derive_rates_from_recorded_counts():
    """验证命中率和质量指标只由已有的公共计数精确计算。"""
    artifacts = analyze_records([record("G4", index=0), record("G4", index=1)])
    memory = artifacts["memory_reuse_detail"][0]
    quality = artifacts["quality_cost_tradeoff"][0]

    assert memory["memory_hit_rate"] == 0.5
    assert memory["memory_reference_id_count"] == 1
    assert quality["task_success"] == 1.0
    assert quality["official_test_pass_rate"] == 1.0


def test_public_metrics_write_csv_and_chinese_report(tmp_path):
    """验证补充分析产物保留稳定 CSV 字段和中文边界说明。"""
    artifacts = analyze_records([record("G1"), record("G4", index=1)])
    for name, rows in artifacts.items():
        write_csv(tmp_path / f"{name}.csv", rows)
        assert (tmp_path / f"{name}.csv").read_text(encoding="utf-8")

    report = tmp_path / "赛题指标补充分析.md"
    write_report(report, artifacts, {"freeze_git_sha": "freeze", "final_record_count": 2})
    content = report.read_text(encoding="utf-8")
    assert "M9 赛题指标补充分析" in content
    assert "`unavailable`" in content
