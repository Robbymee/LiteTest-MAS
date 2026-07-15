"""独立的 StateVector V2：使用固定长度 bytes 传递最小状态。"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import ClassVar


class StateVectorError(ValueError):
    """表示状态向量格式、版本或字段校验失败。"""


@dataclass(frozen=True)
class StateVectorV2:
    """可跨平台确定性编码的 32 字节状态向量。"""

    schema_version: int = 2
    phase: str = "planning"
    source_role: str = "planner"
    target_role: str = "executor"
    progress_code: int = 0
    artifact_flags: int = 0
    error_code: str = "none"
    retry_count: int = 0
    confidence: float = 0.0
    state_reference: str = ""
    memory_reference_count: int = 0

    MAGIC: ClassVar[bytes] = b"SV"
    _STRUCT: ClassVar[struct.Struct] = struct.Struct(">2sBBBBHBBBf16sH")
    PHASES: ClassVar[dict[str, int]] = {"planning": 0, "generation": 1, "validation": 2, "complete": 3, "failed": 4}
    ROLES: ClassVar[dict[str, int]] = {"planner": 0, "retriever": 1, "executor": 2, "summarizer": 3}
    ERRORS: ClassVar[dict[str, int]] = {"none": 0, "parse": 1, "timeout": 2, "runtime": 3, "sandbox": 4, "backend": 5}

    def __post_init__(self) -> None:
        """校验固定字段范围和不应进入状态向量的内容。"""
        if self.schema_version != 2 or self.phase not in self.PHASES or self.source_role not in self.ROLES or self.target_role not in self.ROLES or self.error_code not in self.ERRORS:
            raise StateVectorError("invalid state vector enum or schema")
        if not 0 <= self.progress_code <= 255 or not 0 <= self.artifact_flags <= 65535 or not 0 <= self.retry_count <= 255 or not 0 <= self.memory_reference_count <= 65535:
            raise StateVectorError("state vector integer out of range")
        if not 0.0 <= self.confidence <= 1.0 or len(self.state_reference.encode("ascii", "ignore")) > 16 or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:.-" for char in self.state_reference):
            raise StateVectorError("invalid state vector reference or confidence")

    def encode(self) -> bytes:
        """将状态编码为固定长度、网络字节序的 bytes。"""
        reference = self.state_reference.encode("ascii").ljust(16, b"\0")
        return self._STRUCT.pack(self.MAGIC, self.schema_version, self.PHASES[self.phase], self.ROLES[self.source_role], self.ROLES[self.target_role], self.artifact_flags, self.progress_code, self.ERRORS[self.error_code], self.retry_count, self.confidence, reference, self.memory_reference_count)

    @classmethod
    def decode(cls, payload: bytes) -> "StateVectorV2":
        """校验并解码固定长度 bytes，拒绝非法版本和截断数据。"""
        if len(payload) != cls._STRUCT.size:
            raise StateVectorError("invalid state vector byte length")
        magic, schema, phase, source, target, flags, progress, error, retry, confidence, reference, memory_count = cls._STRUCT.unpack(payload)
        if magic != cls.MAGIC or phase not in cls.PHASES.values() or source not in cls.ROLES.values() or target not in cls.ROLES.values() or error not in cls.ERRORS.values():
            raise StateVectorError("invalid state vector bytes")
        return cls(schema, next(key for key, value in cls.PHASES.items() if value == phase), next(key for key, value in cls.ROLES.items() if value == source), next(key for key, value in cls.ROLES.items() if value == target), progress, flags, next(key for key, value in cls.ERRORS.items() if value == error), retry, confidence, reference.rstrip(b"\0").decode("ascii"), memory_count)

    def equivalent_text_state_bytes(self) -> int:
        """计算同一字段的最小公开文本表示字节数，用于压缩率对比。"""
        text = f"phase={self.phase};source={self.source_role};target={self.target_role};progress={self.progress_code};flags={self.artifact_flags};error={self.error_code};retry={self.retry_count};confidence={self.confidence:.6f};state={self.state_reference};memory={self.memory_reference_count}"
        return len(text.encode("utf-8"))

    def compression_ratio(self) -> float | None:
        """按等价文本字节计算压缩率，分母为零时返回 None。"""
        equivalent = self.equivalent_text_state_bytes()
        return None if equivalent == 0 else 1 - len(self.encode()) / equivalent
