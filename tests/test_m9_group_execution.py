import json
import subprocess
import sys
from pathlib import Path

from experiments.m9_runner import execute_task, plan
from llm.mock_backend import MockLLMBackend
from memory.shared_memory import SharedMemory
from runtime.real_llm_runner import approved_tasks
from state.vector import StateMetrics

ROOT = Path(__file__).resolve().parents[1]


def spec():
    return {"implementation_git_sha": "test", "result_scope": "formal_real_llm_ablation", "model": "mock", "backend": "mock"}


def backend(item):
    paths = {"mbpp": ("datasets/manifests/mbpp_selected_groups.json", "datasets/processed/mbpp/mbpp_tasks.jsonl"), "humaneval": ("datasets/manifests/humaneval_selected_groups.json", "datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl")}
    selection, data = (ROOT / part for part in paths[item["dataset"]])
    task = next(task for task in approved_tasks(selection, data, 0) + approved_tasks(selection, data, 1) if task.task_id == item["task_id"])
    return MockLLMBackend("mock", fixed_response=f"```python\ndef {task.function_name}(*args, **kwargs):\n    return None\n```")


def test_groups_use_distinct_real_prompt_and_state_memory_paths(tmp_path):
    items = plan(ROOT)
    selected = [next(item for item in items if item["seed"] == 42 and item["dataset"] == "mbpp" and item["experiment_group"] == group) for group in ("G1", "G2", "G3", "G4")]
    records = []
    for item in selected[:3]:
        state = StateMetrics(True) if item["experiment_group"] == "G3" else None
        records.append(execute_task(ROOT, item, tmp_path / item["experiment_group"], backend(item), spec(), "freeze", [item], state_metrics=state))
    assert records[0]["communication_mode"] == "text" and records[0]["protocol_event_count"] == 0
    assert records[1]["communication_mode"] == "protocol" and records[1]["protocol_event_count"] == 1
    assert records[2]["state_vector_count"] == 1 and records[2]["state_vector_bytes"] > 0
    g4 = [item for item in items if item["seed"] == 42 and item["dataset"] == "mbpp" and item["experiment_group"] == "G4" and item["group_id"] == selected[3]["group_id"]][:2]
    memory = SharedMemory(dataset="mbpp", group_id=g4[0]["group_id"], seed=42)
    first = execute_task(ROOT, g4[0], tmp_path / "G4", backend(g4[0]), spec(), "freeze", g4, memory=memory, state_metrics=StateMetrics(True))
    second = execute_task(ROOT, g4[1], tmp_path / "G4", backend(g4[1]), spec(), "freeze", g4, memory=memory, state_metrics=StateMetrics(True))
    assert first["memory_write_count"] == 1
    assert second["memory_reference_ids"] and second["memory_hit_count"] == 1


def test_cli_executes_a_complete_mock_combination(tmp_path):
    spec_path = ROOT / "tests" / "fixtures" / "m9_fake_spec.json"
    output = tmp_path / "run"
    run = subprocess.run([
        sys.executable, "scripts/run_m9_experiment.py", "--spec", str(spec_path), "--output-root", str(output),
        "--combination", "G1:mbpp:42", "--strict", "--freeze-git-sha", "fake-freeze",
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["executed"] == 10
    inventory = json.loads((output / "public" / "inventory.json").read_text(encoding="utf8"))
    assert inventory["final_count"] == 10 and not inventory["missing_task_keys"]
    assert (output / "public" / "completion.json").is_file()
