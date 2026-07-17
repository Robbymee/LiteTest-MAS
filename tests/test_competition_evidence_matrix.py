from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "赛题需求与证据矩阵.md"
ALLOWED_STATUSES = {
    "已实现且有正式证据",
    "已实现但证据不足",
    "部分实现",
    "未实现",
    "不适用",
}


def test_competition_evidence_matrix_is_utf8_complete_and_preserves_freeze_boundary():
    """验证赛题证据矩阵完整记录需求并保护 M9 冻结边界。"""
    content = MATRIX.read_text(encoding="utf-8")

    # 43 个编号条目是赛题审计的最小覆盖面，避免文档后续静默漏项。
    rows = [line for line in content.splitlines() if line.startswith("| ") and " | " in line]
    requirement_rows = [line for line in rows if line.split("|")[1].strip().isdigit()]
    assert len(requirement_rows) == 43
    assert {int(line.split("|")[1].strip()) for line in requirement_rows} == set(range(1, 44))

    for row in requirement_rows:
        cells = [cell.strip() for cell in row.split("|")[1:-1]]
        assert len(cells) == 10
        assert cells[7] in ALLOWED_STATUSES

    assert "cc7aac0417afb6acab47baaf7449459692fa9444" in content
    assert "v1.0.0-experiment" in content
    assert "不得填 `0`" in content
    assert "不得从总模型 Token、文本字符或质量结果反推" in content


def test_competition_evidence_matrix_marks_unrecoverable_m9_metrics_unavailable():
    """验证公开记录缺失的分层指标不会被伪造为零值。"""
    content = MATRIX.read_text(encoding="utf-8")

    for field in (
        "protocol_payload_bytes",
        "capability_handshake_count",
        "equivalent_text_state_bytes",
        "memory_accept_count",
        "memory_effective_reuse_rate",
    ):
        assert f"`{field}`" in content
    assert "`unavailable`" in content
