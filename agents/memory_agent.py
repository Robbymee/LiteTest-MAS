from __future__ import annotations

import json
from pathlib import Path

from protocol.messages import AgentMessage


class MemoryAgent:
    name = "MemoryAgent"

    def __init__(self, memory_path: Path) -> None:
        self.memory_path = memory_path

    def remember(self, task: dict, plan: AgentMessage) -> AgentMessage:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "task_id": task["task_id"],
            "function_name": task["function_name"],
            "signature": task["signature"],
            "plan": plan.content,
        }
        existing = []
        if self.memory_path.exists():
            existing = json.loads(self.memory_path.read_text(encoding="utf-8"))
        existing.append(record)
        self.memory_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return AgentMessage(
            sender=self.name,
            receiver="Orchestrator",
            role="memory",
            content=f"Stored context for task {task['task_id']}.",
            metadata={"task_id": task["task_id"], "memory_path": str(self.memory_path)},
        )
