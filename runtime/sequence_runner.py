"""Deterministic M2.2 runner for human-approved MBPP task sequences."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from agents.planner import PlannerAgent
from protocol.adapters import get_adapter


BLOCKED_KEYS = {"hidden_reference_tests", "reference_solution", "canonical_solution", "test_list", "tests"}


class SequenceValidationError(ValueError):
    """The selection manifest or processed task set is not safe to run."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SelectedTask:
    task_id: str
    source_task_id: str
    group_id: str
    function_name: str
    signature: str
    task_description: str

    def agent_view(self, sequence_id: str, round_index: int, global_round_index: int) -> dict[str, Any]:
        view = {
            "task_id": self.task_id,
            "source_task_id": self.source_task_id,
            "group_id": self.group_id,
            "sequence_id": sequence_id,
            "round_index": round_index,
            "global_round_index": global_round_index,
            "task_description": self.task_description,
            "function_name": self.function_name,
            "signature": self.signature,
        }
        if BLOCKED_KEYS & set(view):
            raise SequenceValidationError("Blocked fields entered the agent view.")
        return view


class SelectedTaskLoader:
    def __init__(self, selection_path: Path, tasks_path: Path) -> None:
        self.selection_path = selection_path
        self.tasks_path = tasks_path

    def load(self) -> tuple[dict[str, Any], list[SelectedTask]]:
        if not self.selection_path.is_file():
            raise SequenceValidationError(f"Selection manifest does not exist: {self.selection_path}")
        if not self.tasks_path.is_file():
            raise SequenceValidationError(f"Processed task file does not exist: {self.tasks_path}")
        manifest = json.loads(self.selection_path.read_text(encoding="utf-8"))
        self._validate_manifest(manifest)
        processed = {
            item["task_id"]: item
            for item in (json.loads(line) for line in self.tasks_path.read_text(encoding="utf-8").splitlines() if line.strip())
        }
        tasks: list[SelectedTask] = []
        for group in manifest["groups"]:
            for task_id, expected_name in zip(group["task_ids"], group["expected_function_names"]):
                item = processed.get(task_id)
                if item is None:
                    raise SequenceValidationError(f"Selected task is missing from processed data: {task_id}")
                if item.get("source_dataset") != manifest["source_dataset"]:
                    raise SequenceValidationError(f"Unexpected source dataset for {task_id}")
                if item.get("function_name") != expected_name:
                    raise SequenceValidationError(f"Function mismatch for {task_id}: expected {expected_name}")
                signature = item.get("signature")
                if not isinstance(signature, str) or not signature.startswith(expected_name + "("):
                    raise SequenceValidationError(f"Invalid signature for {task_id}")
                visible = item.get("agent_visible_context")
                if not isinstance(visible, dict) or BLOCKED_KEYS & set(visible):
                    raise SequenceValidationError(f"Unsafe agent-visible context for {task_id}")
                description = visible.get("task_description")
                if not isinstance(description, str):
                    raise SequenceValidationError(f"Missing task description for {task_id}")
                tasks.append(SelectedTask(task_id, str(item["source_task_id"]), group["group_id"], expected_name, signature, description))
        return manifest, tasks

    @staticmethod
    def _validate_manifest(manifest: dict[str, Any]) -> None:
        if manifest.get("selection_status") not in {"human_approved", "delegated_review_approved"}:
            raise SequenceValidationError("selection_status must be an approved review status")
        if not isinstance(manifest.get("source_dataset"), str) or not manifest["source_dataset"]:
            raise SequenceValidationError("selection manifest must declare a source dataset")
        groups = manifest.get("groups")
        if not isinstance(groups, list) or len(groups) != 2 or manifest.get("group_count") != 2:
            raise SequenceValidationError("Selection manifest must contain exactly two groups")
        if manifest.get("tasks_per_group") != 5 or manifest.get("total_tasks") != 10:
            raise SequenceValidationError("Selection manifest must define five tasks per group and ten total tasks")
        group_ids = [group.get("group_id") for group in groups]
        if len(set(group_ids)) != 2:
            raise SequenceValidationError("Group IDs must be unique")
        task_ids = [task_id for group in groups for task_id in group.get("task_ids", [])]
        if len(task_ids) != 10 or len(set(task_ids)) != 10:
            raise SequenceValidationError("Selected task IDs must be exactly ten and unique")
        for group in groups:
            if len(group.get("task_ids", [])) != 5 or len(group.get("expected_function_names", [])) != 5:
                raise SequenceValidationError("Each group must contain five task IDs and function names")
            if group.get("sequence_order") != [1, 2, 3, 4, 5]:
                raise SequenceValidationError("Each group must preserve sequence order 1..5")
        if BLOCKED_KEYS & set(_nested_keys(manifest)):
            raise SequenceValidationError("Selection manifest contains blocked fields")


def _nested_keys(value: Any):
    if isinstance(value, dict):
        yield from value
        for child in value.values():
            yield from _nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_keys(child)


class SequenceRunner:
    def __init__(self, manifest: dict[str, Any], tasks: list[SelectedTask], mode: str, seed: int) -> None:
        if mode not in {"text", "protocol"}:
            raise SequenceValidationError("mode must be text or protocol")
        self.manifest = manifest
        self.tasks = tasks
        self.mode = mode
        self.seed = seed
        self.manifest_hash = hashlib.sha256(self._manifest_bytes()).hexdigest()

    def _manifest_bytes(self) -> bytes:
        return canonical_json(self.manifest).encode("utf-8")

    def build_plan(self) -> dict[str, Any]:
        rounds = []
        task_by_id = {task.task_id: task for task in self.tasks}
        global_index = 0
        groups = []
        for group in self.manifest["groups"]:
            sequence_id = f"{group['group_id']}:seed{self.seed}"
            group_rounds = []
            for round_index, task_id in enumerate(group["task_ids"], start=1):
                global_index += 1
                task = task_by_id[task_id]
                round_data = {"sequence_id": sequence_id, "group_id": group["group_id"], "round_index": round_index, "global_round_index": global_index, "task_id": task.task_id, "function_name": task.function_name, "signature": task.signature}
                rounds.append(round_data)
                group_rounds.append(task_id)
            groups.append({"sequence_id": sequence_id, "group_id": group["group_id"], "task_ids": group_rounds})
        task_plan = {"source_dataset": self.manifest["source_dataset"], "seed": self.seed, "groups": groups, "rounds": rounds}
        return {"schema_version": "1.0", "run_id": f"m2_2_{self.mode}_seed{self.seed}", "source_dataset": self.manifest["source_dataset"], "selection_manifest": self.manifest.get("selection_purpose"), "selection_manifest_sha256": self.manifest_hash, "mode": self.mode, "seed": self.seed, "group_count": 2, "tasks_per_group": 5, "total_rounds": 10, "groups": groups, "rounds": rounds, "task_plan_sha256": sha256_json(task_plan), "plan_sha256": sha256_json({"mode": self.mode, **task_plan})}

    def run(self, output_dir: Path, dry_run: bool = False, continue_on_error: bool = False) -> dict[str, Any]:
        plan = self.build_plan()
        if dry_run:
            return {"plan": plan, "summary": None}
        output_dir.mkdir(parents=True, exist_ok=False)
        (output_dir / "traces").mkdir()
        (output_dir / "sequence_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        task_by_id = {task.task_id: task for task in self.tasks}
        records = []
        for item in plan["rounds"]:
            task = task_by_id[item["task_id"]]
            try:
                safe_view = task.agent_view(item["sequence_id"], item["round_index"], item["global_round_index"])
                message = PlannerAgent().plan({"task_id": task.task_id, "function_name": task.function_name, "cases": []})
                logical_message = {"sender": message.sender, "receiver": message.receiver, "role": message.role, "content": message.content, "metadata": message.metadata}
                encoded = get_adapter(self.mode).encode(message)
                trace_name = f"round_{item['global_round_index']:02d}.json"
                (output_dir / "traces" / trace_name).write_text(json.dumps({"agent_view": safe_view, "logical_messages": [logical_message], "encoded_message": encoded}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                record = {"schema_version": "1.0", "run_id": plan["run_id"], "mode": self.mode, "seed": self.seed, **item, "status": "succeeded", "agent_count": 1, "emitted_message_count": 1, "emitted_event_count": 1, "result_summary": "mock planning round completed", "error_type": None, "error_message": None, "trace_ref": f"traces/{trace_name}"}
            except Exception as error:  # safe error record; no source task data is included
                record = {"schema_version": "1.0", "run_id": plan["run_id"], "mode": self.mode, "seed": self.seed, **item, "status": "failed", "agent_count": 0, "emitted_message_count": 0, "emitted_event_count": 0, "result_summary": "mock planning round failed", "error_type": type(error).__name__, "error_message": str(error), "trace_ref": None}
            deterministic = {key: value for key, value in record.items() if key not in {"trace_ref", "error_message"}}
            record["deterministic_payload_hash"] = sha256_json(deterministic)
            records.append(record)
            if record["status"] == "failed" and not continue_on_error:
                break
        (output_dir / "rounds.jsonl").write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
        succeeded = sum(record["status"] == "succeeded" for record in records)
        failed = sum(record["status"] == "failed" for record in records)
        summary = {"run_id": plan["run_id"], "mode": self.mode, "seed": self.seed, "planned_rounds": 10, "executed_rounds": len(records), "succeeded_rounds": succeeded, "failed_rounds": failed, "skipped_rounds": 0, "group_count": 2, "task_plan_sha256": plan["task_plan_sha256"], "deterministic_result_sha256": sha256_json([{key: value for key, value in record.items() if key not in {"trace_ref", "error_message"}} for record in records]), "completion_status": "complete" if len(records) == 10 and failed == 0 else "incomplete"}
        (output_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"plan": plan, "summary": summary}
