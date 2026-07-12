from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


GROUPS = {"G1": (False, False), "G2": (False, False), "G3": (True, False), "G4": (True, True)}
CANARY_TASKS = {
    "mbpp_g1": (42, "G1", "mbpp", "mbpp_sanitized:591"),
    "humaneval_g4": (42, "G4", "humaneval", "humaneval_plus:HumanEval/27"),
}
DATA = {
    "mbpp": ("datasets/manifests/mbpp_selected_groups.json", "datasets/processed/mbpp/mbpp_tasks.jsonl"),
    "humaneval": ("datasets/manifests/humaneval_selected_groups.json", "datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl"),
}
PUBLIC_RESULT_REQUIRED = {
    "schema_version", "task_id", "dataset", "group_id", "seed", "experiment_group", "plan_index",
    "mode", "state_enabled", "memory_enabled", "implementation_git_sha", "spec_sha256", "freeze_git_sha",
    "model", "backend", "prompt_version", "prompt_sha256", "parser_version", "candidate_sha256",
    "parse_status", "request_ids", "request_count", "finish_reason", "prompt_tokens", "completion_tokens",
    "total_tokens", "usage_available", "latency_seconds", "retry_count", "resume_count", "attempt_count",
    "static_risk_status", "sandbox_started", "sandbox_completed", "official_test_count",
    "official_test_pass_count", "official_test_fail_count", "official_test_pass_rate", "task_success", "timeout",
    "error_category", "exit_code", "execution_time_seconds", "stdout_bytes", "stderr_bytes", "result_scope",
    "final_status", "infrastructure_failure", "model_quality_failure",
}


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def spec_sha256(spec):
    return stable_hash({key: value for key, value in spec.items() if key != "created_at"})


def plan(root):
    from runtime.real_llm_runner import approved_tasks

    items = []
    for seed in (42, 43, 44):
        order = [["G1", "G2", "G3", "G4"], ["G2", "G3", "G4", "G1"], ["G3", "G4", "G1", "G2"]][seed - 42]
        for group in order:
            for dataset in ("mbpp", "humaneval"):
                selection, task_file = (root / value for value in DATA[dataset])
                for task in approved_tasks(selection, task_file, 0) + approved_tasks(selection, task_file, 1):
                    items.append({
                        "seed": seed,
                        "experiment_group": group,
                        "dataset": dataset,
                        "task_id": task.task_id,
                        "group_id": task.group_id,
                    })
    return [{**item, "plan_index": index} for index, item in enumerate(items)]


def task_identity(item):
    return (item["seed"], item["experiment_group"], item["dataset"], item["task_id"])


def task_key(item):
    return stable_hash({"seed": item["seed"], "experiment_group": item["experiment_group"], "dataset": item["dataset"], "task_id": item["task_id"]})[:24]


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf8")
    os.replace(temporary, path)


def verify_inventory(root, spec):
    items = plan(root)
    if len(items) != 240 or len({task_identity(item) for item in items}) != 240:
        raise ValueError("invalid formal plan")
    return items


def validate_spec(spec, implementation_sha):
    required = {
        "schema_version", "experiment_id", "result_scope", "conclusion_scope", "implementation_git_sha", "model",
        "backend", "seeds", "experiment_groups", "generation_parameters", "parser_version", "sandbox_version",
    }
    missing = required - set(spec)
    if missing:
        raise ValueError("spec missing " + ",".join(sorted(missing)))
    if spec["implementation_git_sha"] != implementation_sha:
        raise ValueError("implementation git SHA mismatch")
    if spec["result_scope"] != "formal_real_llm_ablation" or spec["seeds"] != [42, 43, 44] or spec["experiment_groups"] != ["G1", "G2", "G3", "G4"]:
        raise ValueError("invalid frozen experiment configuration")


def select_plan(items, combination=None):
    if combination is None:
        return items
    try:
        group, dataset, seed = combination.split(":")
        selected = [item for item in items if item["experiment_group"] == group and item["dataset"] == dataset and item["seed"] == int(seed)]
    except ValueError as error:
        raise ValueError("invalid combination") from error
    if len(selected) != 10:
        raise ValueError("combination must resolve exactly ten planned tasks")
    return selected


def canary_item(root, name):
    if name not in CANARY_TASKS:
        raise ValueError("unknown canary")
    seed, group, dataset, task_id = CANARY_TASKS[name]
    matches = [item for item in plan(root) if (item["seed"], item["experiment_group"], item["dataset"], item["task_id"]) == (seed, group, dataset, task_id)]
    if len(matches) != 1:
        raise ValueError("invalid fixed canary plan")
    return matches[0]


def rebuild_inventory(public_root, planned):
    files = sorted(Path(public_root).glob("tasks/*.json"))
    rows = []
    for path in files:
        try:
            rows.append((path, json.loads(path.read_text(encoding="utf8"))))
        except json.JSONDecodeError:
            continue
    final = [(path, row) for path, row in rows if str(row.get("final_status", "")).startswith(("completed_", "failed_"))]
    final_keys = [task_key(row) for _, row in final if all(key in row for key in ("seed", "experiment_group", "dataset", "task_id"))]
    planned_keys = [task_key(item) for item in planned]
    duplicates = sorted({key for key in final_keys if final_keys.count(key) > 1})
    payload = {
        "schema_version": "1.0",
        "planned_count": len(planned),
        "final_count": len(final),
        "planned_task_keys": planned_keys,
        "final_task_keys": final_keys,
        "missing_task_keys": [key for key in planned_keys if key not in final_keys],
        "duplicate_task_keys": duplicates,
        "status_counts": {status: sum(row.get("final_status") == status for _, row in final) for status in sorted({row.get("final_status") for _, row in final})},
        "task_result_checksums": {path.stem: hashlib.sha256(path.read_bytes()).hexdigest() for path, _ in rows},
    }
    payload["inventory_sha256"] = stable_hash(payload)
    return payload


def completion_marker(inventory, metadata):
    return {
        "schema_version": "1.0",
        "completion_status": "complete",
        "planned_count": inventory["planned_count"],
        "final_count": inventory["final_count"],
        "inventory_sha256": inventory["inventory_sha256"],
        **metadata,
    }


def write_inventory(public_root, planned, completion_metadata=None, write_completion_marker=True):
    inventory = rebuild_inventory(public_root, planned)
    atomic_write(Path(public_root) / "inventory.json", inventory)
    marker = Path(public_root) / "completion.json"
    complete = not inventory["missing_task_keys"] and not inventory["duplicate_task_keys"] and inventory["final_count"] == len(planned)
    if complete and completion_metadata is not None and write_completion_marker:
        atomic_write(marker, completion_marker(inventory, completion_metadata))
    elif marker.exists():
        marker.unlink()
    return inventory


def final_record(output_root, item):
    path = Path(output_root) / "public" / "tasks" / (task_key(item) + ".json")
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf8"))
    return value if str(value.get("final_status", "")).startswith(("completed_", "failed_")) else None


def group_config(group):
    if group not in GROUPS:
        raise ValueError("unknown experiment group")
    state, memory = GROUPS[group]
    return {"mode": "text" if group == "G1" else "protocol", "state_enabled": state, "memory_enabled": memory}


def _public_eval_defaults(parse_status):
    return {
        "static_risk_status": None,
        "sandbox_started": False,
        "sandbox_completed": False,
        "official_test_count": None,
        "official_test_pass_count": None,
        "official_test_fail_count": None,
        "official_test_pass_rate": None,
        "task_success": False,
        "timeout": False,
        "error_category": parse_status,
        "exit_code": None,
        "execution_time_seconds": None,
        "stdout_bytes": 0,
        "stderr_bytes": 0,
    }


def execute_task(root, item, output_root, backend, spec, freeze_git_sha, planned, write_completion_marker=True):
    from generation.candidate_parser import parse_candidate
    from generation.candidate_prompt import build_prompt
    from llm.models import LLMMessage, LLMRequest
    from runtime.real_llm_runner import approved_tasks
    from sandbox.private_eval import evaluate_private

    selection, data = (root / value for value in DATA[item["dataset"]])
    tasks = approved_tasks(selection, data, 0) + approved_tasks(selection, data, 1)
    task = next(value for value in tasks if value.task_id == item["task_id"])
    private = {value["task_id"]: value for value in map(json.loads, data.read_text(encoding="utf8").splitlines())}[task.task_id]
    key = task_key(item)
    public_tasks = Path(output_root) / "public" / "tasks"
    private_root = Path(output_root) / "private"
    attempts = private_root / "attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    attempt_no = len(list(attempts.glob(key + "-attempt-*.json"))) + 1
    previous = json.loads((public_tasks / (key + ".json")).read_text(encoding="utf8")) if (public_tasks / (key + ".json")).is_file() else {}
    resume_count = int(previous.get("resume_count", 0)) + (1 if previous.get("status") == "running" else 0)
    attempt_metadata = {
        "schema_version": "1.0", "task_key": key, **item,
        "attempt": attempt_no, "resume_count": resume_count, "status": "running",
    }
    atomic_write(attempts / f"{key}-attempt-{attempt_no}.json", attempt_metadata)
    atomic_write(public_tasks / (key + ".json"), {
        "schema_version": "1.0", "status": "running", "task_key": key, **item,
        "attempt_count": attempt_no, "resume_count": resume_count,
    })
    system, prompt, prompt_hash = build_prompt(task)
    response = backend.generate(LLMRequest((LLMMessage("system", system), LLMMessage("user", prompt)), backend.model, temperature=0, max_tokens=256, seed=item["seed"]))
    artifact = parse_candidate(response.text, task.function_name)
    private_root.mkdir(parents=True, exist_ok=True)
    (private_root / (key + ".txt")).write_text(response.text, encoding="utf8")
    evaluation = evaluate_private(private, artifact["candidate_code"]) if artifact["parse_status"] == "success" else _public_eval_defaults(artifact["parse_status"])
    record = {
        "schema_version": "1.0", **item, **group_config(item["experiment_group"]),
        "implementation_git_sha": spec["implementation_git_sha"], "spec_sha256": spec_sha256(spec), "freeze_git_sha": freeze_git_sha,
        "model": spec["model"], "backend": spec["backend"], "prompt_version": "candidate_codegen_v1", "prompt_sha256": prompt_hash,
        "parser_version": artifact["parser_version"], "candidate_sha256": artifact.get("candidate_sha256"), "parse_status": artifact["parse_status"],
        "request_ids": [response.request_id], "request_count": 1, "finish_reason": response.finish_reason,
        "prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens,
        "usage_available": response.usage.usage_available, "latency_seconds": response.latency_seconds, "retry_count": 0,
        "resume_count": resume_count, "attempt_count": attempt_no, "result_scope": spec["result_scope"],
        "final_status": "completed_success" if evaluation["task_success"] else "failed_official_tests", **{key: value for key, value in evaluation.items() if key not in {"task_id", "dataset", "candidate_sha256"}},
        "infrastructure_failure": False, "model_quality_failure": not evaluation["task_success"],
    }
    atomic_write(attempts / f"{key}-attempt-{attempt_no}.json", {
        **attempt_metadata, "status": record["final_status"], "final_status": record["final_status"],
    })
    atomic_write(public_tasks / (key + ".json"), record)
    write_inventory(Path(output_root) / "public", planned, {"spec_sha256": record["spec_sha256"], "freeze_git_sha": freeze_git_sha, "model": spec["model"], "implementation_git_sha": spec["implementation_git_sha"], "result_scope": record["result_scope"]}, write_completion_marker=write_completion_marker)
    return record


def resume_or_execute(root, item, output_root, backend, spec, freeze_git_sha, planned, resume=False, write_completion_marker=True):
    prior = final_record(output_root, item) if resume else None
    if prior is not None:
        return prior, True
    return execute_task(root, item, output_root, backend, spec, freeze_git_sha, planned, write_completion_marker), False
