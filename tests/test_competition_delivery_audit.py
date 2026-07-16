from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.audit_competition_delivery import REQUIRED_DOCUMENTS, audit_markdown, audit_repository, write_report


ROOT = Path(__file__).resolve().parents[1]


def test_markdown_audit_detects_language_encoding_fence_and_link_errors(tmp_path):
    """验证审计器能识别英文主体、坏编码、围栏不闭合和失效链接。"""
    english = tmp_path / "english.md"
    english.write_text("# English\n\nOnly English.\n", encoding="utf-8")
    assert "chinese_body_missing" in audit_markdown(english, tmp_path)["errors"]

    invalid = tmp_path / "invalid.md"
    invalid.write_bytes(b"\xff\xfe")
    assert audit_markdown(invalid, tmp_path)["errors"] == ["invalid_utf8"]

    broken = tmp_path / "broken.md"
    broken.write_text("# 中文\n\n[缺失](missing.md)\n```python\n", encoding="utf-8")
    errors = audit_markdown(broken, tmp_path)["errors"]
    assert "unbalanced_code_fence" in errors
    assert "missing_link:missing.md" in errors


def test_markdown_audit_detects_personal_path_and_real_secret(tmp_path):
    """验证文档中的用户绝对路径和真实凭据形态会被拒绝。"""
    path = tmp_path / "unsafe.md"
    path.write_text("# 中文审计\n\nC:\\Users\\name\\model，api_key=real-secret-value\n", encoding="utf-8")
    errors = audit_markdown(path, tmp_path)["errors"]
    assert "personal_absolute_path" in errors
    assert "credential_value" in errors


def test_repository_audit_reports_real_gaps_and_preserves_protected_revisions(tmp_path):
    """验证审计如实保留剩余交付缺口，同时确认冻结提交和标签仍可解析。"""
    result = audit_repository(ROOT)
    assert result["valid"] is False
    assert result["summary"]["tracked_markdown_count"] >= 30
    assert result["missing_documents"] == []
    assert result["summary"]["markdown_failure_count"] == 0
    assert result["delivery"]["commitment_letter"] is False
    assert result["delivery"]["presentation"] is True
    assert result["delivery"]["video_or_download_instructions"] is True
    assert all(item["valid"] for item in result["protected_revisions"].values())

    report = tmp_path / "report.md"
    write_report(result, report)
    text = report.read_text(encoding="utf-8")
    assert "# 赛事中文文档与交付物审计报告" in text
    assert "valid=false" in text


def test_required_chinese_documents_are_utf8_and_have_chinese_titles():
    """验证总流程要求的中文文档存在、可解码且具有中文一级标题。"""
    for relative in REQUIRED_DOCUMENTS:
        path = ROOT / relative
        text = path.read_bytes().decode("utf-8", errors="strict")
        title = text.splitlines()[0]
        assert title.startswith("# ")
        assert any("\u4e00" <= char <= "\u9fff" for char in title)


def test_audit_cli_supports_incomplete_acceptance(tmp_path):
    """验证 CLI 可区分交付不完整与审计命令执行失败。"""
    report = tmp_path / "audit.md"
    process = subprocess.run(
        [
            sys.executable,
            "scripts/audit_competition_delivery.py",
            "--root",
            ".",
            "--report",
            str(report),
            "--allow-incomplete",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    assert process.returncode == 0
    assert '"valid": false' in process.stdout
    assert report.is_file()
