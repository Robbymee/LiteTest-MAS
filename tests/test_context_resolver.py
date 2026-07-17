from __future__ import annotations

import json

import pytest

from memory.gated_shared_memory_v2 import GatedSharedMemoryV2
from runtime.context_resolver import ExecutionContextError, ExecutionContextRegistry
from state.vector_v2 import StateVectorV2


def state_payload(**overrides) -> bytes:
    """Build a valid executor-bound StateVector payload."""
    values = {
        "phase": "generation",
        "source_role": "planner",
        "target_role": "executor",
        "progress_code": 1,
        "state_reference": "sv_test",
    }
    values.update(overrides)
    return StateVectorV2(**values).encode()


def memory_store(**overrides) -> GatedSharedMemoryV2:
    """Build one isolated memory scope with permissive test thresholds."""
    values = {
        "dataset": "mbpp",
        "task_group": "group-a",
        "seed": 42,
        "experiment_id": "current-main",
        "relevance_threshold": 0.0,
        "confidence_threshold": 0.0,
    }
    values.update(overrides)
    return GatedSharedMemoryV2(**values)


def accepted_memory(store: GatedSharedMemoryV2, *, source_task_id: str = "task-1"):
    """Write and accept one safe public memory for task-2."""
    record = store.write(
        source_agent="Summarizer",
        created_at="2026-07-17",
        task_topic="stable list sorting",
        summary="preserve stable ordering",
        tags=("group-a",),
        task_type="candidate_generation",
        provenance="public-summary",
        confidence=0.9,
        success_status="success",
        source_task_id=source_task_id,
    )
    accepted = store.retrieve(
        task_id="task-2",
        topic="stable list sorting",
        tags=("group-a",),
        task_type="candidate_generation",
    )
    assert accepted == [record]
    return record


def test_state_reference_resolves_and_preserves_executor_fields():
    registry = ExecutionContextRegistry()
    registry.register_state("sv_test", state_payload(retry_count=2, error_code="parse"))

    context = registry.resolve(
        state_vector_id="sv_test",
        memory_ids=(),
        memory=None,
        task_id="task-2",
    )

    assert context.state == {
        "error_code": "parse",
        "phase": "generation",
        "progress_code": 1,
        "retry_count": 2,
    }


@pytest.mark.parametrize(
    "state_id,payload",
    (("missing", None), ("sv_test", b"damaged")),
)
def test_unknown_and_corrupt_state_references_are_rejected(state_id, payload):
    registry = ExecutionContextRegistry()
    if payload is not None:
        registry.register_state(state_id, payload)
    with pytest.raises(ExecutionContextError):
        registry.resolve(
            state_vector_id=state_id,
            memory_ids=(),
            memory=None,
            task_id="task-2",
        )


def test_state_phase_and_target_role_are_enforced():
    registry = ExecutionContextRegistry()
    registry.register_state("sv_phase", state_payload(phase="planning"))
    registry.register_state("sv_role", state_payload(target_role="summarizer"))
    for state_id in ("sv_phase", "sv_role"):
        with pytest.raises(ExecutionContextError, match="executor boundary"):
            registry.resolve(
                state_vector_id=state_id,
                memory_ids=(),
                memory=None,
                task_id="task-2",
            )


def test_memory_reference_resolves_safe_summary_and_exact_prompt_metrics():
    store = memory_store()
    record = accepted_memory(store)
    context = ExecutionContextRegistry().resolve(
        state_vector_id=None,
        memory_ids=(record.memory_id,),
        memory=store,
        task_id="task-2",
    )
    memory_json = context.memory_json()

    assert memory_json is not None
    assert json.loads(memory_json) == [
        {
            "confidence": 0.9,
            "memory_id": record.memory_id,
            "provenance": "public-summary",
            "summary": "preserve stable ordering",
        }
    ]
    assert context.memory_injected_bytes == len(memory_json.encode("utf-8"))
    assert context.memory_injected_tokens == len(memory_json.split())


def test_memory_rejects_failed_self_unknown_cross_scope_and_unsafe_records():
    store = memory_store()
    failed = store.write(
        source_agent="Summarizer",
        created_at="now",
        task_topic="sorting",
        summary="failed strategy",
        tags=("group-a",),
        task_type="candidate_generation",
        provenance="public-summary",
        confidence=1.0,
        success_status="failure",
        source_task_id="task-0",
    )
    self_record = store.write(
        source_agent="Summarizer",
        created_at="now",
        task_topic="sorting",
        summary="self strategy",
        tags=("group-a",),
        task_type="candidate_generation",
        provenance="public-summary",
        confidence=1.0,
        success_status="success",
        source_task_id="task-2",
    )
    assert store.retrieve(
        task_id="task-2",
        topic="sorting",
        tags=("group-a",),
        task_type="candidate_generation",
    ) == []
    for memory_id in (failed.memory_id, self_record.memory_id, "mem2_unknown"):
        with pytest.raises(ValueError, match="isolation or acceptance"):
            store.resolve_accepted((memory_id,), task_id="task-2")

    accepted = accepted_memory(store, source_task_id="task-1")
    other_scope = memory_store(dataset="humaneval")
    with pytest.raises(ValueError, match="isolation or acceptance"):
        other_scope.resolve_accepted((accepted.memory_id,), task_id="task-2")

    accepted.summary = "raw_response must not cross the boundary"
    with pytest.raises(ExecutionContextError, match="invalid memory reference"):
        ExecutionContextRegistry().resolve(
            state_vector_id=None,
            memory_ids=(accepted.memory_id,),
            memory=store,
            task_id="task-2",
        )
