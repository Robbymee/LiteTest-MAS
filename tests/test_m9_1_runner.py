from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.m9_1_runner import _executor_prompt, _protocol_session, _write_public_record, canary_item, execute_item, group_config, metric_defaults, plan, run_batch, select_plan
from memory.gated_shared_memory_v2 import GatedSharedMemoryV2
from experiments.m9_1_verifier import verify
from runtime.context_resolver import ResolvedExecutionContext


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


def test_batch_runner_dry_run_and_checkpoint_scope(tmp_path):
    """验证 240 条批量 dry-run 不调用模型且输出独立 scope。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    result = run_batch(ROOT, spec, tmp_path / "run", "mock", None, dry_run=True)
    assert result["planned"] == 240 and result["dry_run"] is True


def test_batch_runner_records_exceptions_and_resumes(tmp_path, monkeypatch):
    """验证单条异常不会中止批次，且恢复时不会重复调用已完成任务。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))

    def synthetic_execute(_root, _spec, item, output_root, _backend, **_kwargs):
        if item["plan_index"] == 1:
            raise RuntimeError("synthetic failure")
        record = {"schema_version": "1.0", **item, **group_config(item["experiment_group"]), **metric_defaults(), "result_scope": _spec["result_scope"], "freeze_git_sha": "freeze", "implementation_git_sha": _spec["implementation_git_sha"], "task_success": False, "final_status": "failed_official_tests"}
        # 合成执行器复用正式公开记录路径，确保 Strict Verifier 检查真实写入契约。
        _write_public_record(output_root, item, record)
        return record

    monkeypatch.setattr("experiments.m9_1_runner.execute_item", synthetic_execute)
    result = run_batch(ROOT, spec, tmp_path / "run", "mock", "freeze")
    assert result["completed"] == 240
    assert verify(tmp_path / "run", spec, "freeze")["valid"] is True
    checkpoint = json.loads((tmp_path / "run" / "checkpoint.json").read_text(encoding="utf-8"))
    assert any(value["status"] == "infrastructure_failure" for value in checkpoint["completed"].values())
    assert run_batch(ROOT, spec, tmp_path / "run", "mock", "freeze", resume=True)["completed"] == 240


def test_protocol_session_sends_handshake_once_per_related_sequence():
    """验证同一关联任务组复用协议会话，握手只在首条消息中出现。"""
    session = _protocol_session()
    first = session.pop("pending_handshake")
    assert first and session.get("pending_handshake") is None


def test_executor_prompt_injects_resolved_semantics_once_without_private_content():
    """验证引用解析结果只在执行端出现一次且不携带私有字段。"""
    context = ResolvedExecutionContext(
        state={
            "phase": "generation",
            "progress_code": 1,
            "error_code": "none",
            "retry_count": 0,
        },
        reusable_public_memory=(
            {
                "memory_id": "mem2_0001",
                "summary": "use stable ordering",
                "confidence": 1.0,
                "provenance": "public-summary",
            },
        ),
    )
    prompt = _executor_prompt([b'{"task_ref":"t_1","state_vector_id":"sv_1"}'], context)
    lowered = prompt.lower()
    assert prompt.count("resolved_state:") == 1
    assert prompt.count('"phase":"generation"') == 1
    assert prompt.count("use stable ordering") == 1
    assert "hidden_reference_tests" not in lowered
    assert "candidate_code" not in lowered
    assert "raw_response" not in lowered


def test_s4_metric_sources_do_not_overwrite_each_other(tmp_path):
    """验证 S4 的通信、状态、记忆和模型指标可同时保留。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    item = canary_item(spec, "S4", "humaneval")
    memory = GatedSharedMemoryV2(
        dataset=item["dataset"], task_group=item["group_id"], seed=item["seed"],
        experiment_id=spec["experiment_id"], relevance_threshold=0.0,
        confidence_threshold=0.0,
    )
    injected = memory.write(
        source_agent="Summarizer", created_at="before-current-task",
        task_topic="public candidate generation", summary="reuse public strategy",
        tags=(item["group_id"],), task_type="candidate_generation",
        provenance="public-summary", confidence=1.0, success_status="success",
        source_task_id="previous-task",
    )
    # 使用 Mock Backend 覆盖完整计量合并路径，不调用真实模型或暴露私有字段。
    record = execute_item(
        ROOT, spec, item, tmp_path, "mock", freeze_git_sha="freeze",
        result_scope=spec["result_scope"], memory=memory, protocol_session=_protocol_session(),
    )
    for field in (
        "agent_message_count", "protocol_payload_bytes", "state_vector_count",
        "state_vector_bytes", "memory_query_count", "memory_write_count",
        "prompt_tokens", "completion_tokens", "total_tokens", "request_count",
    ):
        assert record[field] != "unavailable"
    expected_memory = ResolvedExecutionContext(
        None,
        ({
            "confidence": 1.0,
            "memory_id": injected.memory_id,
            "provenance": "public-summary",
            "summary": "reuse public strategy",
        },),
    )
    assert record["memory_injected_bytes"] == expected_memory.memory_injected_bytes
    assert record["memory_injected_tokens"] == expected_memory.memory_injected_tokens
    assert record["memory_token_estimator"] == "whitespace_v1"
