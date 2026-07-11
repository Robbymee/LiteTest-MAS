from __future__ import annotations

import json
from typing import Protocol

from protocol.messages import AgentMessage


class MessageAdapter(Protocol):
    def encode(self, message: AgentMessage) -> str:
        ...

    def decode(self, payload: str) -> AgentMessage:
        ...


class TextAdapter:
    def encode(self, message: AgentMessage) -> str:
        return (
            f"From {message.sender} to {message.receiver} as {message.role}: "
            f"{message.content}"
        )

    def decode(self, payload: str) -> AgentMessage:
        return AgentMessage(
            sender="text_adapter",
            receiver="orchestrator",
            role="text",
            content=payload,
            metadata={"format": "text"},
        )


class ProtocolAdapter:
    def encode(self, message: AgentMessage) -> str:
        return message.to_json()

    def decode(self, payload: str) -> AgentMessage:
        return AgentMessage.from_dict(json.loads(payload))


def get_adapter(mode: str) -> MessageAdapter:
    if mode == "text":
        return TextAdapter()
    if mode == "protocol":
        return ProtocolAdapter()
    raise ValueError(f"Unsupported mode: {mode}")
