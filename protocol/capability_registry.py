"""Compact Protocol V2 的本地能力注册表。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


def _canonical(value: Any) -> str:
    """将注册内容转换为跨平台稳定的 JSON。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Capability:
    """描述一个可审计的逻辑 Agent 能力。"""

    capability_id: str
    name: str
    description: str
    actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """返回用于握手和审计的稳定能力描述。"""
        return {"capability_id": self.capability_id, "name": self.name, "description": self.description, "actions": list(self.actions)}


class CapabilityRegistry:
    """注册能力、发现能力并记录远端到本地的协议映射。"""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._remote_mapping: dict[str, str] = {}

    def register(self, name: str, description: str, actions: Iterable[str]) -> Capability:
        """注册一次能力描述，重复注册同一语义时返回原能力。"""
        action_values = tuple(sorted(set(str(action) for action in actions)))
        if not name or not description or not action_values:
            raise ValueError("capability fields must be nonempty")
        payload = {"name": name, "description": description, "actions": action_values}
        capability_id = "cap_" + hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()[:12]
        capability = Capability(capability_id, name, description, action_values)
        existing = self._capabilities.get(capability_id)
        if existing is not None and existing != capability:
            raise ValueError("capability id collision")
        self._capabilities[capability_id] = capability
        return capability

    def discover(self, action: str | None = None) -> list[Capability]:
        """按可选动作过滤并返回稳定排序的能力列表。"""
        values = sorted(self._capabilities.values(), key=lambda item: item.capability_id)
        return [item for item in values if action is None or action in item.actions]

    def get(self, capability_id: str) -> Capability:
        """按本地或映射后的远端 ID 获取能力。"""
        resolved = self._remote_mapping.get(capability_id, capability_id)
        try:
            return self._capabilities[resolved]
        except KeyError as error:
            raise ValueError("unknown capability id") from error

    def map_remote(self, remote_id: str, descriptor: dict[str, Any]) -> str:
        """注册远端能力并建立可审计的 remote ID 映射。"""
        local = self.register(str(descriptor["name"]), str(descriptor["description"]), descriptor["actions"])
        self._remote_mapping[str(remote_id)] = local.capability_id
        return local.capability_id

    def audit(self) -> dict[str, Any]:
        """返回不含私有任务内容的注册与映射快照。"""
        return {"capabilities": [item.to_dict() for item in self.discover()], "remote_mapping": dict(sorted(self._remote_mapping.items()))}
