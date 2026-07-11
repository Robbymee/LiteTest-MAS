import importlib.util
import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "import_humaneval_plus.py"
FIXTURE = PROJECT_ROOT / "datasets" / "fixtures" / "humaneval_plus" / "synthetic_humaneval_plus.jsonl"


def load_module():
    spec = importlib.util.spec_from_file_location("import_humaneval_plus", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_humaneval_import_preserves_provenance_and_isolates_hidden_fields(tmp_path):
    completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--output-dir", str(tmp_path)], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    task = json.loads((tmp_path / "humaneval_plus_tasks.jsonl").read_text(encoding="utf-8"))
    assert task["source_dataset"] == "humaneval_plus"
    assert task["source_task_id"] == "HumanEval/0"
    assert task["function_name"] == "increment"
    assert task["provenance"]["dataset_name"] == "HumanEval+"
    assert "canonical_solution" not in task["agent_visible_context"]
    assert "code_under_test" not in task["agent_visible_context"]
    assert "hidden_reference_tests" not in task["agent_visible_context"]
    assert task["hidden_reference_tests"][0]["test"]


def test_humaneval_import_output_is_stable_and_code_compiles(tmp_path):
    module = load_module()
    record = json.loads(FIXTURE.read_text(encoding="utf-8"))
    first = module._convert(record, module.DEFAULT_SOURCE_URL)
    second = module._convert(record, module.DEFAULT_SOURCE_URL)
    assert first == second
    compile(first["code_under_test"], "<test>", "exec")
