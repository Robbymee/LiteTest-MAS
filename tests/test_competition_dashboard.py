from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.build_competition_dashboard import _embedded_json, build_data, page


ROOT = Path(__file__).resolve().parents[1]


def test_competition_dashboard_builds_public_dual_experiment_data(tmp_path):
    """验证统一数据同时包含 M9 与 M9.1，且不携带私有字段。"""
    result = build_data(ROOT / "reports/m9", ROOT / "reports/m9_1", tmp_path)
    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert result["experiment_count"] == 2
    assert len(result["index_sha256"]) == 64
    assert set(data["experiments"]) == {"m9", "m9_1"}
    assert data["experiments"]["m9"]["manifest"]["strict_verifier"]["valid"] is True
    assert data["experiments"]["m9_1"]["manifest"]["freeze_git_sha"].startswith("c79fd48")
    serialized = json.dumps(data).lower()
    assert "candidate_code" not in serialized and "raw_response" not in serialized
    assert "c:\\users" not in serialized and "/home/" not in serialized
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "LiteTest-MAS 赛事指标 Dashboard" in html
    assert all(value in html for value in ("数据集", "任务组", "Seed", "Strict Verifier", "Freeze SHA", "Spec hash"))
    assert all(value in html for value in ("Prompt Token", "Completion Token", "StateVector", "Memory", "official-test"))
    assert not any(value in html for value in ("innerHTML", "insertAdjacentHTML", "document.write"))
    assert {path.name for path in tmp_path.iterdir()} == {"data.json", "index.html"}


def test_competition_dashboard_rejects_forbidden_csv_field(tmp_path):
    """验证 CSV 字段白名单之前先执行禁止字段检查。"""
    m9 = tmp_path / "m9"
    m9.mkdir()
    for source in (ROOT / "reports/m9").iterdir():
        if source.is_file():
            (m9 / source.name).write_bytes(source.read_bytes())
    path = m9 / "quality_cost_tradeoff.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*rows[0], "raw_response"])
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="forbidden_public_field"):
        build_data(m9, ROOT / "reports/m9_1", tmp_path / "output")


def test_competition_dashboard_keeps_unavailable_values(tmp_path):
    """验证缺失指标保持 unavailable，不被转换为零。"""
    build_data(ROOT / "reports/m9", ROOT / "reports/m9_1", tmp_path)
    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    s1 = data["experiments"]["m9_1"]["groups"][0]
    assert s1["agent_text_tokens"] == "unavailable"
    assert "unavailable" in (tmp_path / "index.html").read_text(encoding="utf-8")


def test_competition_dashboard_escapes_embedded_html():
    """验证嵌入数据不能提前结束 JSON 节点或形成可执行 HTML。"""
    attack = "</script><img src=x onerror=alert(1)>"
    data = {"experiments": {"x": {"label": attack}}}
    serialized = _embedded_json(data)
    html = page(data)
    assert attack not in serialized and attack not in html
    assert json.loads(serialized)["experiments"]["x"]["label"] == attack


def test_competition_dashboard_rejects_paths_and_credentials(tmp_path):
    """验证安全字段中的绝对路径和凭据值同样被拒绝。"""
    m9 = tmp_path / "m9"
    m9.mkdir()
    for source in (ROOT / "reports/m9").iterdir():
        if source.is_file():
            (m9 / source.name).write_bytes(source.read_bytes())
    path = m9 / "quality_cost_tradeoff.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    rows[0]["dataset"] = "C:\\Users\\name\\private"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="forbidden_public_value"):
        build_data(m9, ROOT / "reports/m9_1", tmp_path / "output")
