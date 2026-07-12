from pathlib import Path

from experiments.m9_runner import atomic_write, plan, rebuild_inventory, select_plan, task_key, verify_inventory


def test_plan_is_fixed_240_and_atomic(tmp_path):
    items = plan(Path("."))
    assert len(items) == 240
    assert len({(item["seed"], item["experiment_group"], item["dataset"], item["task_id"]) for item in items}) == 240
    assert [item["plan_index"] for item in items] == list(range(240))
    atomic_write(tmp_path / "task.json", {"status": "completed"})
    assert (tmp_path / "task.json").exists() and not (tmp_path / "task.tmp").exists()


def test_combination_selection_and_composite_inventory_identity(tmp_path):
    spec = {
        "schema_version": "1", "experiment_id": "x", "result_scope": "formal_real_llm_ablation",
        "conclusion_scope": "fixed_task_fixed_model_ablation", "implementation_git_sha": "sha", "model": "m", "backend": "mock",
        "seeds": [42, 43, 44], "experiment_groups": ["G1", "G2", "G3", "G4"], "generation_parameters": {},
        "parser_version": "candidate_parser_v1", "sandbox_version": "private_subprocess_v1",
    }
    items = verify_inventory(Path("."), spec)
    selected = select_plan(items, "G1:mbpp:42")
    assert len(selected) == 10
    first = selected[0]
    clone = {**first, "seed": 43}
    atomic_write(tmp_path / "tasks" / f"{task_key(first)}.json", {**first, "final_status": "completed_success"})
    atomic_write(tmp_path / "tasks" / f"{task_key(clone)}.json", {**clone, "final_status": "completed_success"})
    inventory = rebuild_inventory(tmp_path, [first, clone])
    assert inventory["final_count"] == 2
    assert not inventory["missing_task_keys"]
    assert not inventory["duplicate_task_keys"]
