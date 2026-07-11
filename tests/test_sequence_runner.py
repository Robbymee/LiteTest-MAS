import json
from pathlib import Path

import pytest

from runtime.sequence_runner import SelectedTaskLoader, SequenceRunner, SequenceValidationError


def write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    groups = []
    records = []
    for group_number in (1, 2):
        ids = []
        names = []
        for index in range(1, 6):
            task_id = f"mbpp_sanitized:{group_number}{index}"
            name = f"function_{group_number}_{index}"
            ids.append(task_id)
            names.append(name)
            records.append({
                "task_id": task_id,
                "source_task_id": f"{group_number}{index}",
                "source_dataset": "mbpp_sanitized",
                "function_name": name,
                "signature": f"{name}(value)",
                "hidden_reference_tests": ["assert hidden_test()"],
                "agent_visible_context": {"task_description": f"Safe task {group_number}-{index}", "function_name": name, "signature": f"{name}(value)"},
            })
        groups.append({"group_id": f"group_{group_number}", "task_ids": ids, "expected_function_names": names, "sequence_order": [1, 2, 3, 4, 5]})
    manifest = {"schema_version": "1.0", "source_dataset": "mbpp_sanitized", "selection_status": "human_approved", "group_count": 2, "tasks_per_group": 5, "total_tasks": 10, "groups": groups}
    manifest_path = tmp_path / "selection.json"
    tasks_path = tmp_path / "tasks.jsonl"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tasks_path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
    return manifest_path, tasks_path


def load_runner(tmp_path: Path, mode: str = "text", seed: int = 42) -> SequenceRunner:
    manifest_path, tasks_path = write_fixture(tmp_path)
    manifest, tasks = SelectedTaskLoader(manifest_path, tasks_path).load()
    return SequenceRunner(manifest, tasks, mode, seed)


def test_loader_and_plan_preserve_two_groups_and_order(tmp_path):
    runner = load_runner(tmp_path)
    plan = runner.build_plan()
    assert plan["total_rounds"] == 10
    assert [round_["round_index"] for round_ in plan["rounds"][:5]] == [1, 2, 3, 4, 5]
    assert [round_["global_round_index"] for round_ in plan["rounds"]] == list(range(1, 11))
    assert plan["rounds"][0]["sequence_id"] != plan["rounds"][5]["sequence_id"]
    assert plan["rounds"][0]["task_id"] == "mbpp_sanitized:11"
    assert plan["rounds"][-1]["task_id"] == "mbpp_sanitized:25"


@pytest.mark.parametrize("mutation", ["status", "duplicate", "missing", "function"])
def test_loader_rejects_invalid_manifest_or_processed_data(tmp_path, mutation):
    manifest_path, tasks_path = write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in tasks_path.read_text(encoding="utf-8").splitlines()]
    if mutation == "status":
        manifest["selection_status"] = "pending"
    elif mutation == "duplicate":
        manifest["groups"][1]["task_ids"][0] = manifest["groups"][0]["task_ids"][0]
    elif mutation == "missing":
        records = records[:-1]
    else:
        records[0]["function_name"] = "wrong"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    tasks_path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
    with pytest.raises(SequenceValidationError):
        SelectedTaskLoader(manifest_path, tasks_path).load()


def test_text_and_protocol_share_task_plan_and_record_deterministically(tmp_path):
    text = load_runner(tmp_path / "text", "text")
    protocol = load_runner(tmp_path / "protocol", "protocol")
    assert text.build_plan()["task_plan_sha256"] == protocol.build_plan()["task_plan_sha256"]
    first = text.run(tmp_path / "first")
    second = text.run(tmp_path / "second")
    protocol_result = protocol.run(tmp_path / "protocol-run")
    assert first["summary"]["completion_status"] == "complete"
    assert first["summary"]["executed_rounds"] == 10
    assert first["summary"]["skipped_rounds"] == 0
    assert first["summary"]["deterministic_result_sha256"] == second["summary"]["deterministic_result_sha256"]
    assert protocol_result["summary"]["task_plan_sha256"] == first["summary"]["task_plan_sha256"]
    rounds = (tmp_path / "first" / "rounds.jsonl").read_text(encoding="utf-8")
    assert "hidden_reference_tests" not in rounds
    assert "assert hidden_test" not in rounds


def test_dry_run_has_plan_but_no_agent_output_files(tmp_path):
    runner = load_runner(tmp_path)
    result = runner.run(tmp_path / "dry", dry_run=True)
    assert len(result["plan"]["rounds"]) == 10
    assert result["summary"] is None
    assert not (tmp_path / "dry").exists()
