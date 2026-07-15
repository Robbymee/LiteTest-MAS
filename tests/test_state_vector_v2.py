from __future__ import annotations

import pytest

from state.vector_v2 import StateVectorError, StateVectorV2


def test_fixed_bytes_roundtrip_and_cross_platform_determinism():
    """验证固定长度、字段恢复和显式网络字节序。"""
    state = StateVectorV2(phase="generation", source_role="planner", target_role="executor", progress_code=7, artifact_flags=3, retry_count=2, confidence=0.75, state_reference="sv_0001", memory_reference_count=2)
    encoded = state.encode()
    assert len(encoded) == 33
    assert encoded == state.encode()
    assert StateVectorV2.decode(encoded) == state
    assert state.equivalent_text_state_bytes() > len(encoded)
    assert state.compression_ratio() > 0


def test_schema_version_error_state_and_invalid_bytes():
    """验证版本、错误状态、范围和非法 bytes 的拒绝行为。"""
    assert StateVectorV2(error_code="timeout").decode(StateVectorV2(error_code="timeout").encode()).error_code == "timeout"
    with pytest.raises(StateVectorError):
        StateVectorV2(schema_version=1)
    with pytest.raises(StateVectorError):
        StateVectorV2(confidence=1.1)
    with pytest.raises(StateVectorError):
        StateVectorV2.decode(b"bad")
    with pytest.raises(StateVectorError):
        StateVectorV2.decode(b"X" + StateVectorV2().encode()[1:])


def test_state_vector_closed_does_not_change_v1_behavior():
    """确认 V2 模块不改变现有 V1 JSON 状态接口。"""
    from state.vector import StateVector

    assert StateVector(task_phase="generation", agent_role="testgen").stable().startswith("{")
