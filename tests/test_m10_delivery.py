from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_m10_delivery import audit
from scripts.build_m10_dashboard import build


ROOT = Path(__file__).resolve().parents[1]


def write_aggregate(root):
    root.mkdir()
    manifest = {
        "result_scope": "formal_real_llm_ablation", "model": "local-model", "freeze_git_sha": "freeze",
        "spec_sha256": "spec", "final_record_count": 240, "strict_verifier": {"valid": True},
        "bootstrap": {"resamples": 2000, "confidence": 0.95, "seed": 1},
        "aggregate_input_sha256": "input", "deterministic_aggregate_sha256": "aggregate",
    }
    groups = [{
        "experiment_group": f"G{index}", "task_count": 60, "task_success_count": 30 + index,
        "task_success_rate": (30 + index) / 60, "official_test_pass_rate": 0.5, "mean_total_tokens": 100.0,
        "mean_latency_seconds": 1.0, "mean_state_vector_bytes": 0.0, "mean_memory_hit_count": 0.0,
        "mean_memory_reuse_count": 0.0, "model_quality_failure_count": 0, "infrastructure_failure_count": 0,
    } for index in range(1, 5)]
    comparisons = [{
        "treatment_group": "G2", "control_group": "G1", "metric": metric, "mean_difference": 0.1,
        "ci_lower": 0.0, "ci_upper": 0.2, "paired_count": 60, "bootstrap_resamples": 2000, "confidence": 0.95,
    } for metric in ("task_success", "official_test_pass_rate", "total_tokens", "latency_seconds")]
    values = {
        "m9_aggregate_manifest.json": manifest, "m9_aggregate_groups.json": groups,
        "m9_aggregate_datasets.json": [], "m9_aggregate_seeds.json": [], "m9_paired_comparisons.json": comparisons,
    }
    for name, value in values.items():
        (root / name).write_text(json.dumps(value), encoding="utf-8")


def test_dashboard_uses_sanitized_aggregate_and_delivery_audit_passes(tmp_path):
    aggregate = tmp_path / "aggregate"
    write_aggregate(aggregate)
    delivery = tmp_path / "delivery"
    result = build(aggregate, delivery)
    assert result["final_record_count"] == 240
    assert "LiteTest-MAS M9 Results" in (delivery / "index.html").read_text(encoding="utf-8")
    assert audit(delivery)["valid"] is True
    cli = subprocess.run([sys.executable, "scripts/audit_m10_delivery.py", "--delivery-dir", str(delivery)], cwd=ROOT, text=True, capture_output=True)
    assert cli.returncode == 0
    assert json.loads(cli.stdout)["valid"] is True


def test_dashboard_rejects_forbidden_aggregate_field(tmp_path):
    aggregate = tmp_path / "aggregate"
    write_aggregate(aggregate)
    groups = json.loads((aggregate / "m9_aggregate_groups.json").read_text(encoding="utf-8"))
    groups[0]["raw_response"] = "blocked"
    (aggregate / "m9_aggregate_groups.json").write_text(json.dumps(groups), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden_aggregate_field"):
        build(aggregate, tmp_path / "delivery")


def test_delivery_audit_rejects_paths_and_credentials(tmp_path):
    delivery = tmp_path / "delivery"
    delivery.mkdir()
    (delivery / "index.html").write_text("C:\\Users\\name api_key=secret", encoding="utf-8")
    (delivery / "data.json").write_text(json.dumps({"strict_verifier": {"valid": True}}), encoding="utf-8")
    result = audit(delivery)
    assert not result["valid"]
    assert any(error.startswith("absolute_path") for error in result["errors"])
    assert any(error.startswith("credential_pattern") for error in result["errors"])
