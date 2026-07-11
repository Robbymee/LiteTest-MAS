from protocol.adapters import ProtocolAdapter, TextAdapter
from protocol.messages import AgentMessage


def test_agent_message_json_roundtrip():
    message = AgentMessage(
        sender="PlannerAgent",
        receiver="TestGenAgent",
        role="plan",
        content="Create tests.",
        metadata={"task_id": "A01"},
    )

    restored = AgentMessage.from_json(message.to_json())

    assert restored.sender == "PlannerAgent"
    assert restored.receiver == "TestGenAgent"
    assert restored.metadata["task_id"] == "A01"


def test_protocol_adapter_decodes_structured_payload():
    message = AgentMessage("a", "b", "role", "content")
    adapter = ProtocolAdapter()

    restored = adapter.decode(adapter.encode(message))

    assert restored.to_dict() == message.to_dict()


def test_text_adapter_produces_readable_text():
    message = AgentMessage("a", "b", "role", "hello")
    text = TextAdapter().encode(message)

    assert "From a to b" in text
    assert "hello" in text
