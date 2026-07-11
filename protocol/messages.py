from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any


@dataclass(frozen=True)
class AgentMessage:
    sender: str
    receiver: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        return cls(
            sender=str(data["sender"]),
            receiver=str(data["receiver"]),
            role=str(data["role"]),
            content=str(data["content"]),
            metadata=dict(data.get("metadata", {})),
            timestamp=str(data.get("timestamp") or datetime.now(timezone.utc).isoformat()),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "AgentMessage":
        return cls.from_dict(json.loads(payload))
