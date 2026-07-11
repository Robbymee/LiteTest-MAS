import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_mbpp.py"
FIXTURE_DIR = PROJECT_ROOT / "datasets" / "fixtures" / "mbpp"


def load_importer_module():
    spec = importlib.util.spec_from_file_location("import_mbpp", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def importer():
    return load_importer_module()


def read_tasks(output_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (output_dir / "mbpp_tasks.jsonl").read_text(encoding="utf-8").splitlines()]


def run_import(input_path: Path, output_dir: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--input", str(input_path), "--output-dir", str(output_dir), *extra_args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_json_fixture_generates_unified_tasks(importer, tmp_path):
    output_dir = tmp_path / "json-output"
    result = importer.import_mbpp(FIXTURE_DIR / "synthetic_mbpp.json")
    importer.write_outputs(result, output_dir, FIXTURE_DIR / "synthetic_mbpp.json")

    tasks = read_tasks(output_dir)
    assert [task["source_task_id"] for task in tasks] == ["101", "102"]
    assert [task["task_id"] for task in tasks] == ["mbpp_sanitized:101", "mbpp_sanitized:102"]
    assert all(task["source_dataset"] == "mbpp_sanitized" for task in tasks)
    assert all(task["provenance"]["original_task_id"] == task["source_task_id"] for task in tasks)
    assert all(task["entry_point"] == task["function_name"] for task in tasks)
    assert all(task["signature"].startswith(task["function_name"] + "(") for task in tasks)
    assert all(compile(task["code_under_test"], "<test>", "exec") for task in tasks)


def test_jsonl_fixture_records_invalid_sample_in_non_strict_mode(tmp_path):
    output_dir = tmp_path / "jsonl-output"
    completed = run_import(FIXTURE_DIR / "synthetic_mbpp.jsonl", output_dir)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert len(read_tasks(output_dir)) == 2
    errors = json.loads((output_dir / "import_errors.json").read_text(encoding="utf-8"))
    summary = json.loads((output_dir / "import_summary.json").read_text(encoding="utf-8"))
    assert len(errors) == 1
    assert "does not compile" in errors[0]["error"]
    assert summary["error_count"] == 1
    assert summary["imported_task_count"] == 2


def test_strict_mode_fails_but_writes_error_report(tmp_path):
    output_dir = tmp_path / "strict-output"
    completed = run_import(FIXTURE_DIR / "synthetic_mbpp.jsonl", output_dir, "--strict")

    assert completed.returncode == 1
    assert "strict mode" in completed.stdout
    assert (output_dir / "import_errors.json").exists()


def test_agent_visible_context_excludes_hidden_tests_and_risk_tags_do_not_depend_on_them(importer):
    records = json.loads((FIXTURE_DIR / "synthetic_mbpp.json").read_text(encoding="utf-8"))
    original = importer.convert_record(records[0])
    changed_tests = dict(records[0])
    changed_tests["test_list"] = ["assert a deliberately different hidden condition"]
    changed = importer.convert_record(changed_tests)

    assert "hidden_reference_tests" not in original["agent_visible_context"]
    assert original["hidden_reference_tests"] != changed["hidden_reference_tests"]
    assert original["risk_tags"] == changed["risk_tags"]
    assert "hidden" not in json.dumps(original["agent_visible_context"])


def test_output_order_and_limit_are_stable(importer, tmp_path):
    input_path = FIXTURE_DIR / "synthetic_mbpp.json"
    first = importer.import_mbpp(input_path, limit=1)
    second = importer.import_mbpp(input_path, limit=1)
    assert first.tasks == second.tasks
    assert [task["source_task_id"] for task in first.tasks] == ["101"]

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    importer.write_outputs(first, first_dir, input_path)
    importer.write_outputs(second, second_dir, input_path)
    assert (first_dir / "mbpp_tasks.jsonl").read_bytes() == (second_dir / "mbpp_tasks.jsonl").read_bytes()


def test_missing_input_returns_clear_failure(tmp_path):
    completed = run_import(tmp_path / "missing.json", tmp_path / "output")

    assert completed.returncode == 2
    assert "does not exist" in completed.stdout
