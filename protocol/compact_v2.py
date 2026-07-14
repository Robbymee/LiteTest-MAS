"""独立的 Compact Protocol V2：通过 registry 减少重复 Agent 间文本。"""

from __future__ import annotations

import json
from typing import Any, Iterable

from protocol.capability_registry import CapabilityRegistry
from protocol.protocol_metrics import ProtocolMetrics
from protocol.reference_registry import ReferenceRegistry


VERSION = "compact_protocol_v2"
_BLOCKED = {"hidden_reference_tests", "private", "candidate_code", "raw_response", "canonical_solution", "expected_output", "traceback", "api_key", "authorization"}


class ProtocolVersionError(ValueError):
    """表示对端未协商到可支持的协议版本。"""


def _stable_bytes(value: dict[str, Any]) -> bytes:
    """以确定性 UTF-8 JSON 序列化协议消息。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _validate_public(value: Any) -> None:
    """拒绝私有评测、候选代码和凭据相关字段进入 V2 消息。"""
    if isinstance(value, dict):
        for key, item in value.items():
            if any(blocked in str(key).lower() for blocked in _BLOCKED):
                raise ValueError("unsafe protocol field")
            _validate_public(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_public(item)
    elif isinstance(value, str) and any(blocked in value.lower() for blocked in _BLOCKED):
        raise ValueError("unsafe protocol content")


class CompactProtocolV2:
    """维护 sequence 级握手、能力映射和一次性引用注册的 V2 协议端点。"""

    def __init__(self, supported_versions: Iterable[str] = (VERSION,)) -> None:
        self.supported_versions = tuple(sorted(set(supported_versions)))
        if VERSION not in self.supported_versions:
            raise ValueError("compact_protocol_v2 must be supported")
        self.capabilities = CapabilityRegistry()
        self.references = ReferenceRegistry()
        self.metrics = ProtocolMetrics()
        self._negotiated_version: str | None = None
        self._handshake_sent = False

    def register_capability(self, name: str, description: str, actions: Iterable[str]) -> str:
        """预注册将在握手中一次性发布的能力并返回 capability_id。"""
        return self.capabilities.register(name, description, actions).capability_id

    def begin_sequence(self, peer_versions: Iterable[str]) -> bytes:
        """协商版本并只生成一次包含能力描述的握手消息。"""
        if self._handshake_sent:
            raise ValueError("handshake already sent for this sequence")
        common = sorted(set(self.supported_versions) & set(peer_versions))
        if VERSION not in common:
            raise ProtocolVersionError("unsupported protocol version")
        self._negotiated_version = VERSION
        payload = _stable_bytes({"v": VERSION, "t": "handshake", "c": [item.to_dict() for item in self.capabilities.discover()]})
        self._handshake_sent = True
        self.metrics.record_handshake(payload)
        return payload

    def receive_handshake(self, payload: bytes) -> dict[str, Any]:
        """接收握手、校验版本并建立远端能力映射。"""
        message = self._decode_raw(payload)
        if message.get("t") != "handshake":
            raise ValueError("expected handshake")
        for descriptor in message.get("c", []):
            self.capabilities.map_remote(str(descriptor["capability_id"]), descriptor)
        self._negotiated_version = VERSION
        return self.capabilities.audit()

    def encode_task_registration(self, task: dict[str, Any]) -> bytes:
        """一次性注册静态公开任务信息，后续 action 仅传 task_ref。"""
        self._require_handshake()
        _validate_public(task)
        task_ref = self.references.register("task", task)
        return self._encode({"t": "task_register", "q": task_ref, "i": task}, reference_count=1)

    def encode_reference_registration(self, value: Any) -> bytes:
        """一次性注册可复用公共参数，后续 action 仅传 reference_id。"""
        self._require_handshake()
        _validate_public(value)
        reference_id = self.references.register("reference", value)
        return self._encode({"t": "reference_register", "x": reference_id, "i": value}, reference_count=1)

    def encode_action(self, *, action: str, sender: str, receiver: str, capability_id: str, task_ref: str, inputs: dict[str, Any] | None = None, result: dict[str, Any] | None = None, state_vector_id: str | None = None, memory_id: str | None = None, reference_ids: Iterable[str] = ()) -> bytes:
        """编码动作、输入和结果；省略空值与默认字段，只保留 registry 引用。"""
        self._require_handshake()
        capability = self.capabilities.get(capability_id)
        if action not in capability.actions:
            raise ValueError("action is not declared by capability")
        self.references.resolve(task_ref)
        references = tuple(sorted(set(str(item) for item in reference_ids)))
        for reference_id in references:
            self.references.resolve(reference_id)
        body = {"t": "action", "a": action, "s": sender, "r": receiver, "c": capability_id, "q": task_ref}
        if inputs:
            _validate_public(inputs)
            body["i"] = inputs
        if result:
            _validate_public(result)
            body["o"] = result
        if state_vector_id:
            body["z"] = state_vector_id
        if memory_id:
            body["m"] = memory_id
        if references:
            body["x"] = list(references)
        return self._encode(body, reference_count=2 + len(references) + int(bool(state_vector_id)) + int(bool(memory_id)))

    def decode(self, payload: bytes) -> dict[str, Any]:
        """解码并恢复注册引用；未知版本、能力或引用都会明确拒绝。"""
        message = self._decode_raw(payload)
        kind = message["t"]
        if kind == "handshake":
            self.receive_handshake(payload)
            return {"type": "handshake", "capabilities": self.capabilities.discover()}
        if kind == "task_register":
            self.references.accept(str(message["q"]), message["i"])
            return {"type": kind, "task_ref": message["q"]}
        if kind == "reference_register":
            self.references.accept(str(message["x"]), message["i"])
            return {"type": kind, "reference_id": message["x"]}
        if kind != "action":
            raise ValueError("unknown compact message type")
        capability = self.capabilities.get(str(message["c"]))
        if message["a"] not in capability.actions:
            raise ValueError("undeclared action")
        restored = {"type": "action", "action": message["a"], "sender": message["s"], "receiver": message["r"], "capability": capability.to_dict(), "task": self.references.resolve(str(message["q"]))}
        for compact, expanded in (("i", "inputs"), ("o", "result"), ("z", "state_vector_id"), ("m", "memory_id")):
            if compact in message:
                restored[expanded] = message[compact]
        if "x" in message:
            restored["references"] = [self.references.resolve(reference_id) for reference_id in message["x"]]
        return restored

    def audit(self) -> dict[str, Any]:
        """输出本地 registry 与通信指标，不含任务和参数原文。"""
        return {"version": self._negotiated_version, "capabilities": self.capabilities.audit(), "references": self.references.audit(), "metrics": self.metrics.as_dict()}

    def _require_handshake(self) -> None:
        if self._negotiated_version != VERSION:
            raise ProtocolVersionError("handshake required")

    def _encode(self, body: dict[str, Any], *, reference_count: int) -> bytes:
        payload = _stable_bytes({"v": VERSION, **body})
        self.metrics.record_payload(payload, len(_stable_bytes({"v": VERSION, "t": body["t"]})), reference_count)
        return payload

    @staticmethod
    def _decode_raw(payload: bytes) -> dict[str, Any]:
        try:
            message = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("invalid compact payload") from error
        if message.get("v") != VERSION:
            raise ProtocolVersionError("unsupported protocol version")
        _validate_public(message)
        return message
