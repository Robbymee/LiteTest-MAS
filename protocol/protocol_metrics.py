"""Compact Protocol V2 的通信层字节统计。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProtocolMetrics:
    """记录 V2 可审计的握手、载荷和引用计数。"""

    handshake_count: int = 0
    handshake_bytes: int = 0
    payload_count: int = 0
    payload_bytes: int = 0
    header_bytes: int = 0
    reference_id_count: int = 0

    def record_handshake(self, payload: bytes) -> None:
        """记录 sequence 内唯一握手的字节数。"""
        self.handshake_count += 1
        self.handshake_bytes += len(payload)

    def record_payload(self, payload: bytes, header_bytes: int, reference_count: int) -> None:
        """记录普通协议载荷和其引用数量。"""
        self.payload_count += 1
        self.payload_bytes += len(payload)
        self.header_bytes += header_bytes
        self.reference_id_count += reference_count

    def as_dict(self) -> dict[str, int]:
        """返回稳定的指标字段。"""
        return {
            "capability_handshake_count": self.handshake_count,
            "capability_handshake_bytes": self.handshake_bytes,
            "protocol_payload_count": self.payload_count,
            "protocol_payload_bytes": self.payload_bytes,
            "protocol_header_bytes": self.header_bytes,
            "reference_id_count": self.reference_id_count,
        }
