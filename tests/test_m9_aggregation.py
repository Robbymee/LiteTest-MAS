from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.m9_runner import PUBLIC_RESULT_REQUIRED, group_config, spec_sha256, task_key, verify_inventory, write_inventory
from scripts.aggregate_m9_results import aggregate, bootstrap_mean_ci


ROOT = Path(__file__).resolve().parents[1]


def fake_spec() -> dict:
    spec = json.loads((ROOT / "tests/fixtures/m9_fake_spec.json").read_text(encoding="utf8"))
    spec.update({
        "bootstrap": {"confidence": 0.95, "resamples": 25, "seed": 1234},
        "task_plan_count": 240,
        "task_plan_sha256": "fake-plan",
    })
    return spec


def record(item: dict, spec: dict) -> dict:
    values = {field: None for field in PUBLIC_RESULT_REQUIRED}
    group = item["experiment_group"]
    success = group in {"G2", "G4"}
    values.update({
        "schema_version": "1.0", **item, **group_config(group),
        "implementation_git_sha": spec["implementation_git_sha"], "spec_sha256": spec_sha256(spec),
        "freeze_git_sha": "fake-freeze", "model": spec["model"], "backend": spec["backend"],
        "prompt_version": "candidate_codegen_v1", "prompt_sha256": "prompt", "parser_version": "candidate_parser_v1",
        "candidate_sha256": "candidate", "parse_status": "success", "request_ids": [], "request_count": 1,
        "finish_reason": "stop", "prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30 + int(group[-1]),
        "usage_available": True, "latency_seconds": float(int(group[-1])), "retry_count": 0, "resume_count": 0,
        "attempt_count": 1, "static_risk_status": "clear", "sandbox_started": True, "sandbox_completed": True,
        "official_test_count": 2, "official_test_pass_count": 2 if success else 1,
        "official_test_fail_count": 0 if success else 1, "official_test_pass_rate": 1.0 if success else 0.5,
        "task_success": success, "timeout": False, "error_category": None, "exit_code": 0,
        "execution_time_seconds": 0.1, "stdout_bytes": 0, "stderr_bytes": 0, "result_scope": spec["result_scope"],
        "final_status": "completed_success" if success else "failed_official_tests", "infrastructure_failure": False,
        "model_quality_failure": not success, "communication_mode": "text" if group == "G1" else "protocol",
        "message_count": 1, "text_character_count": 100 + int(group[-1]), "protocol_event_count": 0 if group == "G1" else 1,
        "state_vector_count": 1 if group in {"G3", "G4"} else 0, "state_vector_bytes": 64 if group in {"G3", "G4"} else 0,
        "memory_reference_ids": [], "memory_read_count": 1 if group == "G4" else 0,
        "memory_hit_count": 1 if group == "G4" else 0, "memory_reuse_count": 1 if group == "G4" else 0,
        "memory_write_count": 1 if group == "G4" else 0,
    })
    return values


def make_run(tmp_path: Path, spec: dict) -> Path:
    run_root = tmp_path / "run"
    public = run_root / "public"
    planned = verify_inventory(ROOT, spec)
    for item in planned:
        path = public / "tasks" / f"{task_key(item)}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record(item, spec), sort_keys=True), encoding="utf8")
    write_inventory(public, planned, {
        "spec_sha256": spec_sha256(spec), "freeze_git_sha": "fake-freeze", "model": spec["model"],
        "implementation_git_sha": spec["implementation_git_sha"], "result_scope": spec["result_scope"],
    })
    return run_root


def test_aggregate_full_public_run_and_paired_bootstrap_are_deterministic(tmp_path):
    spec = fake_spec()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf8")
    run_root = make_run(tmp_path, spec)
    first = aggregate(run_root, spec_path, tmp_path / "first", "fake-freeze")
    second = aggregate(run_root, spec_path, tmp_path / "second", "fake-freeze")
    assert first["final_record_count"] == 240
    assert first["strict_verifier"]["valid"] is True
    assert first["deterministic_aggregate_sha256"] == second["deterministic_aggregate_sha256"]
    comparisons = json.loads((tmp_path / "first" / "m9_paired_comparisons.json").read_text(encoding="utf8"))
    assert len(comparisons) == 40
    success = next(item for item in comparisons if item["treatment_group"] == "G2" and item["control_group"] == "G1" and item["metric"] == "task_success")
    assert success["paired_count"] == 60
    assert success["mean_difference"] == 1.0
    assert success["ci_lower"] == success["ci_upper"] == 1.0
    assert len(json.loads((tmp_path / "first" / "m9_aggregate_tasks.json").read_text(encoding="utf8"))) == 240


def test_aggregate_rejects_forbidden_nested_public_data(tmp_path):
    spec = fake_spec()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf8")
    run_root = make_run(tmp_path, spec)
    first = next((run_root / "public" / "tasks").glob("*.json"))
    value = json.loads(first.read_text(encoding="utf8"))
    value["safe"] = {"hidden_reference_tests": "not allowed"}
    first.write_text(json.dumps(value), encoding="utf8")
    with pytest.raises(ValueError, match="strict_verifier_failed|forbidden_public_fields"):
        aggregate(run_root, spec_path, tmp_path / "output", "fake-freeze")


def test_bootstrap_mean_ci_uses_requested_seed_and_confidence():
    first = bootstrap_mean_ci([0.0, 1.0, 2.0], resamples=100, confidence=0.95, seed=10)
    second = bootstrap_mean_ci([0.0, 1.0, 2.0], resamples=100, confidence=0.95, seed=10)
    assert first == second
    assert first["paired_count"] == 3
    assert first["ci_lower"] <= first["mean_difference"] <= first["ci_upper"]
