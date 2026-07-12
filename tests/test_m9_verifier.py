import json
import subprocess
import sys

from experiments.m9_runner import PUBLIC_RESULT_REQUIRED, group_config, spec_sha256, task_key, verify_inventory, write_inventory
from scripts.verify_m9_run import verify

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def fake_spec():
    return json.loads((ROOT / "tests/fixtures/m9_fake_spec.json").read_text(encoding="utf8"))


def public_record(item, spec):
    record = {key: None for key in PUBLIC_RESULT_REQUIRED}
    record.update({
        "schema_version": "1.0", **item, **group_config(item["experiment_group"]),
        "implementation_git_sha": spec["implementation_git_sha"], "spec_sha256": spec_sha256(spec), "freeze_git_sha": "fake-freeze",
        "model": spec["model"], "backend": spec["backend"], "prompt_version": "candidate_codegen_v1", "prompt_sha256": "prompt",
        "parser_version": "candidate_parser_v1", "candidate_sha256": None, "parse_status": "success", "request_ids": [], "request_count": 0,
        "usage_available": False, "retry_count": 0, "resume_count": 0, "attempt_count": 1,
        "static_risk_status": "clear", "sandbox_started": True, "sandbox_completed": True,
        "official_test_count": 1, "official_test_pass_count": 1, "official_test_fail_count": 0, "official_test_pass_rate": 1.0,
        "task_success": True, "timeout": False, "error_category": None, "exit_code": 0, "execution_time_seconds": 0.0,
        "stdout_bytes": 0, "stderr_bytes": 0, "result_scope": spec["result_scope"], "final_status": "completed_success",
        "infrastructure_failure": False, "model_quality_failure": False,
    })
    return record


def make_run(tmp_path, planned, spec, completion=False):
    public = tmp_path / "public"
    for item in planned:
        path = public / "tasks" / f"{task_key(item)}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(public_record(item, spec), sort_keys=True), encoding="utf8")
    metadata = {
        "spec_sha256": spec_sha256(spec), "freeze_git_sha": "fake-freeze", "model": spec["model"],
        "implementation_git_sha": spec["implementation_git_sha"], "result_scope": spec["result_scope"],
    } if completion else None
    write_inventory(public, planned, metadata)
    return public


def test_full_strict_verifier_accepts_complete_240_public_run(tmp_path):
    spec = fake_spec()
    planned = verify_inventory(ROOT, spec)
    make_run(tmp_path, planned, spec, completion=True)
    result = verify(tmp_path, spec, strict=True, expected_freeze_sha="fake-freeze")
    assert result["valid"] and result["planned_count"] == result["final_count"] == 240


def test_combination_strict_verifier_accepts_exactly_ten_public_records(tmp_path):
    spec = fake_spec()
    planned = [item for item in verify_inventory(ROOT, spec) if item["experiment_group"] == "G1" and item["dataset"] == "mbpp" and item["seed"] == 42]
    make_run(tmp_path, planned, spec)
    result = verify(tmp_path, spec, strict=True, combination="G1:mbpp:42", expected_freeze_sha="fake-freeze")
    assert result["valid"] and result["planned_count"] == result["final_count"] == 10


def test_verifier_rejects_missing_duplicate_schema_mapping_inventory_and_marker_errors(tmp_path):
    spec = fake_spec()
    planned = verify_inventory(ROOT, spec)
    public = make_run(tmp_path, planned, spec, completion=True)
    first = public / "tasks" / f"{task_key(planned[0])}.json"
    row = json.loads(first.read_text(encoding="utf8"))
    row.pop("backend")
    row["mode"] = "protocol"
    first.write_text(json.dumps(row), encoding="utf8")
    duplicate = public / "tasks" / "duplicate.json"
    duplicate.write_text(json.dumps(public_record(planned[0], spec)), encoding="utf8")
    (public / "completion.json").unlink()
    result = verify(tmp_path, spec, strict=True, expected_freeze_sha="wrong-freeze")
    assert not result["valid"]
    assert "missing_public_schema:" + first.name in result["errors"]
    assert "combination_mode_mismatch:" + first.name in result["errors"]
    assert "duplicate_tasks" in result["errors"]
    assert "inventory_mismatch" in result["errors"]
    assert "completion_marker_mismatch" in result["errors"]
    assert any(error.startswith("freeze_sha_mismatch:") for error in result["errors"])


def test_verifier_cli_uses_spec_plan_not_task_file_plan(tmp_path):
    spec = fake_spec()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf8")
    planned = verify_inventory(ROOT, spec)
    make_run(tmp_path / "run", planned, spec, completion=True)
    result = subprocess.run([
        sys.executable, "scripts/verify_m9_run.py", "--run-root", str(tmp_path / "run"), "--spec", str(spec_path),
        "--strict", "--expected-freeze-sha", "fake-freeze",
    ], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["planned_count"] == 240
