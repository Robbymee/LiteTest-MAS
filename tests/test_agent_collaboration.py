from __future__ import annotations

from agents.collaboration import build_role_events
from protocol.messages import AgentMessage


def test_role_events_record_real_logical_chain_fields():
    """验证角色事件来自现有消息 sender，并包含要求的协作字段。"""
    messages = [
        AgentMessage("PlannerAgent", "TestGenAgent", "plan", "plan", {"task_id": "public:1"}, "2026-01-01T00:00:00+00:00"),
        AgentMessage("MemoryAgent", "Orchestrator", "memory", "stored", {"task_id": "public:1"}, "2026-01-01T00:00:01+00:00"),
        AgentMessage("TestGenAgent", "ExecutorAgent", "test_generation", "generated", {"task_id": "public:1"}, "2026-01-01T00:00:02+00:00"),
        AgentMessage("ExecutorAgent", "SummarizerAgent", "execution", "finished", {"task_id": "public:1"}, "2026-01-01T00:00:03+00:00"),
        AgentMessage("SummarizerAgent", "Orchestrator", "summary", "summarized", {"task_id": "public:1"}, "2026-01-01T00:00:04+00:00"),
    ]
    events = build_role_events(messages)
    assert [event.role_id for event in events] == ["planner", "retriever", "testgen", "executor", "summarizer"]
    assert all(event.capability_id and event.action and event.input_reference and event.output_reference for event in events)
    assert all(event.status == "completed" for event in events)


def test_unknown_sender_is_explicitly_not_fabricated():
    """未知消息必须标记 unmapped，不能伪装成已知 Agent。"""
    event = build_role_events([AgentMessage("Unknown", "x", "role", "content", {"task_id": "public:1"}, "t")])[0]
    assert event.role_id == "unknown" and event.status == "unmapped"
