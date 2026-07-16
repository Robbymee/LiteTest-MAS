from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PPTX = ROOT / "LiteTest-MAS赛事演示.pptx"
VIDEO = ROOT / "LiteTest-MAS演示视频.mp4"


def test_competition_presentation_is_real_editable_pptx():
    """验证赛事 PPTX 是可编辑的十页中文 Open XML 演示文稿。"""
    assert PPTX.stat().st_size > 25_000
    with zipfile.ZipFile(PPTX) as archive:
        names = archive.namelist()
        slides = [name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        assert len(slides) == 10
        text = b"".join(archive.read(name) for name in slides).decode("utf-8")
        assert "LiteTest-MAS" in text
        assert "StateVector V2" in text
        assert "负迁移" in text


def test_competition_video_is_real_mp4_without_private_content():
    """验证演示视频具有 MP4 容器签名、实际体积且不携带私有字段。"""
    content = VIDEO.read_bytes()
    assert len(content) > 500_000
    assert b"ftyp" in content[:64]
    lowered = content.lower()
    for forbidden in (b"hidden_reference_tests", b"candidate_code", b"raw_response", b"c:\\users\\", b"/home/"):
        assert forbidden not in lowered
