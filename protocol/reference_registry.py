"""Compact Protocol V2 的静态任务和重复参数引用注册表。"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical(value: Any) -> str:
    """生成跨平台稳定的 JSON 表示。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class ReferenceRegistry:
    """以稳定短 ID 保存一次性任务和参数注册，并支持恢复。"""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def register(self, namespace: str, value: Any) -> str:
        """注册值并返回由内容决定的稳定引用 ID。"""
        if namespace not in {"task", "reference"}:
            raise ValueError("unsupported reference namespace")
        reference_id = f"{namespace[:1]}_" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()[:12]
        existing = self._values.get(reference_id)
        if existing is not None and _canonical(existing) != _canonical(value):
            raise ValueError("reference id collision")
        self._values[reference_id] = value
        return reference_id

    def resolve(self, reference_id: str) -> Any:
        """恢复已注册值，未知引用明确报错。"""
        try:
            return self._values[reference_id]
        except KeyError as error:
            raise ValueError("unknown reference id") from error

    def accept(self, reference_id: str, value: Any) -> None:
        """接收远端注册并校验其引用 ID 与内容一致。"""
        namespace = "task" if reference_id.startswith("t_") else "reference" if reference_id.startswith("r_") else ""
        if not namespace or self.register(namespace, value) != reference_id:
            raise ValueError("invalid reference registration")

    def audit(self) -> dict[str, str]:
        """返回引用 ID 与值摘要哈希，不暴露注册内容。"""
        return {key: hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest() for key, value in sorted(self._values.items())}
