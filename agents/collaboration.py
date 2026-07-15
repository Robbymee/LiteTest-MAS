"""从真实 AgentMessage 调用链生成可审计的逻辑角色事件。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from protocol.messages import AgentMessage


@dataclass(frozen=True)
class RoleEvent:
    """记录一个逻辑角色的公开协作事件，不代表一次独立 LLM 调用。"""

    role_id: str
    capability_id: str
    action: str
    input_reference: str
    output_reference: str
    started_at: str
    completed_at: str
    status: str

    def to_dict(self) -> dict[str, str]:
        """返回稳定的公开事件字段。"""
        return asdict(self)


_MAPPING: dict[str, tuple[str, str, str, str]] = {
    "PlannerAgent": ("planner", "planner.plan", "task", "plan"),
    "MemoryAgent": ("retriever", "memory.store_context", "task", "memory_refs"),
    "TestGenAgent": ("testgen", "executor.generate_candidate", "plan", "candidate_artifact"),
    "ExecutorAgent": ("executor", "executor.sandbox", "candidate_artifact", "sandbox_result"),
    "SummarizerAgent": ("summarizer", "summarizer.public_summary", "sandbox_result", "public_summary"),
}


def build_role_events(messages: Iterable[AgentMessage]) -> list[RoleEvent]:
    """将现有消息映射为真实调用链事件，并保留未知消息的显式状态。"""
    events: list[RoleEvent] = []
    for message in messages:
        mapping = _MAPPING.get(message.sender)
        task_id = str(message.metadata.get("task_id", "unknown"))
        if mapping is None:
            events.append(RoleEvent("unknown", "unknown", message.role, task_id, "unmapped", message.timestamp, message.timestamp, "unmapped"))
            continue
        role_id, capability_id, input_kind, output_kind = mapping
        events.append(RoleEvent(role_id, capability_id, mapping[1].split(".", 1)[1], f"{input_kind}:{task_id}", f"{output_kind}:{task_id}", message.timestamp, message.timestamp, "completed"))
    return events
