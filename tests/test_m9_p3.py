import json
import subprocess
import sys

import pytest

from experiments.m9_runner import DATA, canary_item, execute_task, resume_or_execute, task_key, write_inventory
from llm.mock_backend import MockLLMBackend
from runtime.real_llm_runner import approved_tasks
from scripts.verify_m9_canary import verify

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def canary_spec():
    return {
        "schema_version": "1.0", "experiment_id": "p3-test", "result_scope": "m9_runner_canary",
        "conclusion_scope": "runner_integration_validation_only", "implementation_git_sha": "test-sha",
        "model": "mock-m9-canary-v1", "backend": "mock", "generation_parameters": {},
        "parser_version": "candidate_parser_v1", "sandbox_version": "private_subprocess_v1",
    }


def candidate_backend(item):
    selection, tasks = (ROOT / value for value in DATA[item["dataset"]])
    task = next(value for value in approved_tasks(selection, tasks, 0) + approved_tasks(selection, tasks, 1) if value.task_id == item["task_id"])
    return MockLLMBackend("mock-m9-canary-v1", fixed_response=f"```python\ndef {task.function_name}(*args, **kwargs):\n    return None\n```")


class InterruptingBackend:
    model = "mock-m9-canary-v1"

    def generate(self, request):
        raise RuntimeError("synthetic interruption")


class NeverBackend:
    model = "mock-m9-canary-v1"

    def generate(self, request):
        raise AssertionError("a final task must not call the backend on resume")


def test_interrupted_attempt_resumes_without_losing_metadata_or_recalling_final(tmp_path):
    item = canary_item(ROOT, "mbpp_g1")
    spec = canary_spec()
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        execute_task(ROOT, item, tmp_path, InterruptingBackend(), spec, "not-a-freeze", [item], write_completion_marker=False)
    key = task_key(item)
    running = json.loads((tmp_path / "public" / "tasks" / f"{key}.json").read_text(encoding="utf8"))
    first_attempt = json.loads((tmp_path / "private" / "attempts" / f"{key}-attempt-1.json").read_text(encoding="utf8"))
    assert running["status"] == "running" and running["task_key"] == key
    assert first_attempt["status"] == "running" and first_attempt["resume_count"] == 0
    record, skipped = resume_or_execute(ROOT, item, tmp_path, candidate_backend(item), spec, "not-a-freeze", [item], resume=True, write_completion_marker=False)
    assert not skipped and record["attempt_count"] == 2 and record["resume_count"] == 1
    assert json.loads((tmp_path / "private" / "attempts" / f"{key}-attempt-1.json").read_text(encoding="utf8")) == first_attempt
    assert verify(tmp_path, "mbpp_g1")["valid"]
    final, skipped = resume_or_execute(ROOT, item, tmp_path, NeverBackend(), spec, "not-a-freeze", [item], resume=True, write_completion_marker=False)
    assert skipped and final["final_status"] == record["final_status"]
    assert not (tmp_path / "public" / "completion.json").exists()


def test_multi_task_inventory_is_consistent_after_canary_execution(tmp_path):
    first = canary_item(ROOT, "mbpp_g1")
    second = canary_item(ROOT, "humaneval_g4")
    spec = canary_spec()
    execute_task(ROOT, first, tmp_path, candidate_backend(first), spec, "not-a-freeze", [first, second], write_completion_marker=False)
    execute_task(ROOT, second, tmp_path, candidate_backend(second), spec, "not-a-freeze", [first, second], write_completion_marker=False)
    inventory = json.loads((tmp_path / "public" / "inventory.json").read_text(encoding="utf8"))
    assert inventory["final_count"] == 2 and not inventory["missing_task_keys"]
    assert set(inventory["final_task_keys"]) == {task_key(first), task_key(second)}
    assert not (tmp_path / "public" / "completion.json").exists()


def test_mock_canary_cli_and_public_verifier(tmp_path):
    output = tmp_path / "run"
    run = subprocess.run([
        sys.executable, "scripts/run_m9_canary.py", "--canary", "mbpp_g1", "--backend", "mock", "--output-root", str(output),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["result_scope"] == "m9_runner_canary" and payload["parse_status"] == "success"
    checked = subprocess.run([
        sys.executable, "scripts/verify_m9_canary.py", "--run-root", str(output), "--canary", "mbpp_g1",
    ], cwd=ROOT, text=True, capture_output=True)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["leakage_count"] == 0
