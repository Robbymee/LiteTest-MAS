from __future__ import annotations

import pytest

from protocol.adapters import ProtocolAdapter, TextAdapter
from protocol.compact_v2 import CompactProtocolV2, ProtocolVersionError
from protocol.messages import AgentMessage


def connected_pair() -> tuple[CompactProtocolV2, CompactProtocolV2, str]:
    """构造已完成 V2 握手的两个合成端点。"""
    sender = CompactProtocolV2()
    receiver = CompactProtocolV2()
    capability_id = sender.register_capability("planner", "分析公开任务并生成计划", ("plan",))
    receiver.receive_handshake(sender.begin_sequence(("compact_protocol_v2",)))
    sender.receive_handshake(receiver.begin_sequence(("compact_protocol_v2",)))
    return sender, receiver, capability_id


def test_handshake_capability_discovery_mapping_and_version_rejection():
    """验证一次握手、能力发现/映射和未知版本拒绝。"""
    sender = CompactProtocolV2()
    capability_id = sender.register_capability("planner", "分析公开任务", ("plan",))
    receiver = CompactProtocolV2()
    receiver.receive_handshake(sender.begin_sequence(("compact_protocol_v2",)))
    assert receiver.capabilities.get(capability_id).name == "planner"
    assert sender.metrics.as_dict()["capability_handshake_count"] == 1
    with pytest.raises(ValueError):
        sender.begin_sequence(("compact_protocol_v2",))
    with pytest.raises(ProtocolVersionError):
        CompactProtocolV2().begin_sequence(("protocol_v1",))


def test_registry_references_defaults_stable_serialization_and_roundtrip():
    """验证任务、重复参数、状态和记忆引用可恢复且空字段会省略。"""
    sender, receiver, capability_id = connected_pair()
    task = {"task_id": "public:1", "description": "公开说明"}
    task_payload = sender.encode_task_registration(task)
    task_ref = receiver.decode(task_payload)["task_ref"]
    parameter_payload = sender.encode_reference_registration({"language": "python"})
    reference_id = receiver.decode(parameter_payload)["reference_id"]
    action = sender.encode_action(action="plan", sender="Planner", receiver="Executor", capability_id=capability_id, task_ref=task_ref, state_vector_id="sv_1", memory_id="m_1", reference_ids=(reference_id,))
    restored = receiver.decode(action)
    assert restored["task"] == task and restored["references"] == [{"language": "python"}]
    assert restored["state_vector_id"] == "sv_1" and restored["memory_id"] == "m_1"
    assert b'"i"' not in action and b'"o"' not in action
    assert action == sender.encode_action(action="plan", sender="Planner", receiver="Executor", capability_id=capability_id, task_ref=task_ref, state_vector_id="sv_1", memory_id="m_1", reference_ids=(reference_id,))
    assert sender.metrics.as_dict()["protocol_payload_bytes"] >= len(action)


def test_private_fields_are_rejected_and_v1_text_mode_are_unchanged():
    """验证 V2 不接收私有字段，且既有 V1 与 Text Mode 保持原行为。"""
    sender, _, capability_id = connected_pair()
    task_ref = sender.references.register("task", {"task_id": "public:1"})
    with pytest.raises(ValueError):
        sender.encode_action(action="plan", sender="Planner", receiver="Executor", capability_id=capability_id, task_ref=task_ref, inputs={"hidden_reference_tests": "x"})
    message = AgentMessage("a", "b", "role", "hello")
    assert ProtocolAdapter().decode(ProtocolAdapter().encode(message)).to_dict() == message.to_dict()
    assert "hello" in TextAdapter().encode(message)
