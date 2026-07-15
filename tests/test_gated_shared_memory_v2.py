from __future__ import annotations

import pytest

from memory.gated_shared_memory_v2 import GatedSharedMemoryV2


def memory(**kwargs) -> GatedSharedMemoryV2:
    """构造固定实验隔离范围的 V2 Memory。"""
    return GatedSharedMemoryV2(dataset="mbpp", task_group="group-a", seed=42, experiment_id="m9_1", **kwargs)


def test_metadata_success_gate_threshold_topk_budget_and_abstain():
    """验证成功门控、阈值、top_k、token budget 和无结果 abstain。"""
    store = memory(top_k=1, relevance_threshold=0.2, confidence_threshold=0.8, token_budget=3)
    store.write(source_agent="Summarizer", created_at="2026-01-01", task_topic="list sorting", summary="use stable order", tags=("list", "sort"), task_type="algorithm", provenance="public-summary", confidence=0.9, success_status="success", source_task_id="task-1")
    store.write(source_agent="Summarizer", created_at="2026-01-01", task_topic="list sorting", summary="failed strategy", tags=("list",), task_type="algorithm", provenance="public-summary", confidence=1.0, success_status="failure", source_task_id="task-2")
    accepted = store.retrieve(task_id="task-3", topic="list sorting", tags=("list", "sort"), task_type="algorithm")
    assert len(accepted) == 1 and accepted[0].success_status == "success"
    assert store.retrieve(task_id="task-4", topic="unrelated", tags=("unrelated",), task_type="other") == []
    assert store.metrics.memory_abstain_count == 1


def test_dataset_seed_group_experiment_and_self_isolation():
    """验证 dataset、task_group、seed、experiment 和自己刚写入记忆的隔离。"""
    store = memory(relevance_threshold=0.0, confidence_threshold=0.0)
    record = store.write(source_agent="Summarizer", created_at="now", task_topic="lists", summary="safe strategy", tags=("lists",), task_type="algorithm", provenance="public", confidence=1.0, success_status="success", source_task_id="task-1")
    assert store.retrieve(task_id="task-1", topic="lists", tags=("lists",), task_type="algorithm") == []
    store.reuse(record.memory_id, task_id="task-2", task_success=True)
    with pytest.raises(ValueError):
        store.reuse(record.memory_id, task_id="task-1", task_success=True)
    assert store.metrics.as_dict()["memory_effective_reuse_rate"] == 1.0


def test_private_field_rejection_eviction_and_no_memory_normal_operation():
    """验证私有字段拒绝、FIFO eviction 和空 Memory 正常 abstain。"""
    store = memory(max_records=1)
    with pytest.raises(ValueError):
        store.write(source_agent="x", created_at="now", task_topic="x", summary="candidate_code", tags=(), task_type="x", provenance="public", confidence=1.0, success_status="success", source_task_id="x")
    store.write(source_agent="x", created_at="now", task_topic="x", summary="safe", tags=("x",), task_type="x", provenance="public", confidence=1.0, success_status="success", source_task_id="1")
    store.write(source_agent="x", created_at="now", task_topic="y", summary="safe", tags=("y",), task_type="y", provenance="public", confidence=1.0, success_status="success", source_task_id="2")
    assert store.metrics.memory_eviction_count == 1
    assert store.retrieve(task_id="3", topic="none", tags=("none",), task_type="none") == []
