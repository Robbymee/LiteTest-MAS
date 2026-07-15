"""M9.1 独立 Runner 的计划和 S1-S4 语义，不复用 M9 G1-G4 配置。"""

from __future__ import annotations

from typing import Any
import json
import hashlib
from pathlib import Path
import sys

from protocol.compact_v2 import CompactProtocolV2
from state.vector_v2 import StateVectorV2
from memory.gated_shared_memory_v2 import GatedSharedMemoryV2


GROUPS = ("S1", "S2", "S3", "S4")


def group_config(group: str) -> dict[str, Any]:
    """返回 M9.1 实验组的独立组件配置。"""
    configs = {
        "S1": {"mode": "text", "state_enabled": False, "memory_enabled": False, "component": "text_baseline"},
        "S2": {"mode": "protocol", "state_enabled": False, "memory_enabled": False, "component": "compact_protocol_v2"},
        "S3": {"mode": "protocol", "state_enabled": True, "memory_enabled": False, "component": "compact_protocol_v2+state_vector_v2"},
        "S4": {"mode": "protocol", "state_enabled": True, "memory_enabled": True, "component": "compact_protocol_v2+state_vector_v2+gated_shared_memory_v2"},
    }
    if group not in configs:
        raise ValueError("unknown M9.1 experiment group")
    return dict(configs[group])


def plan(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """从 M9.1 Spec 返回不可变语义上的公开任务计划。"""
    if spec.get("experiment_groups") != list(GROUPS) or spec.get("task_plan_count") != 240:
        raise ValueError("invalid M9.1 plan scope")
    items = [dict(item) for item in spec["task_plan"]]
    if len(items) != 240 or len({(x["seed"], x["experiment_group"], x["dataset"], x["task_id"]) for x in items}) != 240:
        raise ValueError("invalid M9.1 task plan")
    return items


def select_plan(spec: dict[str, Any], combination: str | None = None) -> list[dict[str, Any]]:
    """按 S 组、数据集和 seed 选择十个公开任务。"""
    items = plan(spec)
    if combination is None:
        return items
    group, dataset, seed_text = combination.split(":")
    selected = [item for item in items if item["experiment_group"] == group and item["dataset"] == dataset and item["seed"] == int(seed_text)]
    if len(selected) != 10:
        raise ValueError("combination must resolve exactly ten tasks")
    return selected


def canary_item(spec: dict[str, Any], group: str, dataset: str, seed: int = 42) -> dict[str, Any]:
    """返回固定公开 canary 任务，不读取私有评测字段。"""
    item = next((item for item in plan(spec) if item["experiment_group"] == group and item["dataset"] == dataset and item["seed"] == seed), None)
    if item is None:
        raise ValueError("canary task not found")
    return item


def execute_item(root: Path, spec: dict[str, Any], item: dict[str, Any], output_root: Path, backend_name: str) -> dict[str, Any]:
    """执行一项固定 M9.1 canary，使用真实 Backend 时只写公开结果。"""
    if backend_name not in {"mock", "openai_compatible"}:
        raise ValueError("unsupported canary backend")
    from generation.candidate_parser import parse_candidate
    from llm.config import LLMConfig, create_backend
    from llm.models import LLMMessage, LLMRequest
    from experiments.m9_runner import DATA
    from runtime.real_llm_runner import approved_tasks
    from sandbox.private_eval import evaluate_private

    group, dataset = item["experiment_group"], item["dataset"]
    selection, data_path = (root / value for value in DATA[dataset])
    task = next(value for value in approved_tasks(selection, data_path, 0) + approved_tasks(selection, data_path, 1) if value.task_id == item["task_id"])
    public_fields = {"task_id": task.task_id, "function_name": task.function_name, "signature": task.signature, "description": task.task_description}
    system = "You are a Python benchmark solver. Return code only."
    text = f"Implement this Python function. Return code only.\nFunction: {task.function_name}\nSignature: {task.signature}\nDescription: {task.task_description}"
    state = StateVectorV2(phase="generation", source_role="planner", target_role="executor", progress_code=1, state_reference="sv_canary") if group in {"S3", "S4"} else None
    memory = GatedSharedMemoryV2(dataset=dataset, task_group=task.group_id, seed=42, experiment_id=spec["experiment_id"]) if group == "S4" else None
    memory_records = memory.retrieve(task_id=task.task_id, topic=task.task_description, tags=(task.group_id,), task_type="candidate_generation") if memory else []
    if group == "S1":
        prompt = text
    else:
        endpoint = CompactProtocolV2()
        capability_id = endpoint.register_capability("executor", "执行公开候选生成动作", ("generate",))
        endpoint.begin_sequence(("compact_protocol_v2",))
        task_ref_payload = endpoint.encode_task_registration(public_fields)
        task_ref = endpoint.references.register("task", public_fields)
        prompt_payload = endpoint.encode_action(action="generate", sender="Planner", receiver="Executor", capability_id=capability_id, task_ref=task_ref, inputs={"state_vector_id": "sv_canary" if state else None, "memory_ids": [record.memory_id for record in memory_records]})
        prompt = "Use this structured public protocol payload and return code only.\n" + prompt_payload.decode("utf-8")
    backend = create_backend(LLMConfig.from_env()) if backend_name == "openai_compatible" else create_backend(LLMConfig(backend="mock"))
    response = backend.generate(LLMRequest((LLMMessage("system", system), LLMMessage("user", prompt)), backend.model, temperature=0, max_tokens=spec["generation_parameters"]["max_tokens"], seed=42))
    artifact = parse_candidate(response.text, task.function_name)
    private = {value["task_id"]: value for value in map(json.loads, data_path.read_text(encoding="utf-8").splitlines())}[task.task_id]
    evaluation = evaluate_private(private, artifact["candidate_code"]) if artifact["parse_status"] == "success" else {"task_success": False, "official_test_count": 0, "official_test_pass_count": 0}
    if memory:
        memory.write(source_agent="Summarizer", created_at="canary", task_topic=task.task_description, summary="公开策略摘要", tags=(task.group_id,), task_type="candidate_generation", provenance="canary", confidence=1.0, success_status="success" if evaluation["task_success"] else "failure", source_task_id=task.task_id)
    record = {"schema_version": "1.0", **item, **group_config(group), "result_scope": "m9_1_real_canary", "backend": backend_name, "model": spec["model"], "parse_status": artifact["parse_status"], "candidate_sha256": artifact.get("candidate_sha256"), "task_success": bool(evaluation["task_success"]), "official_test_count": evaluation.get("official_test_count"), "official_test_pass_count": evaluation.get("official_test_pass_count"), "prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens, "latency_seconds": response.latency_seconds, "public_leakage_count": 0}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / f"{item['plan_index']:03d}_{group}_{dataset}_{task.task_id.replace(':', '_').replace('/', '_')}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def execute_canary(root: Path, spec: dict[str, Any], group: str, dataset: str, output_root: Path, backend_name: str) -> dict[str, Any]:
    """执行一项固定 canary；正式批量循环使用 execute_item。"""
    return execute_item(root, spec, canary_item(spec, group, dataset), output_root, backend_name)


def task_key(item: dict[str, Any]) -> str:
    """生成不含任务原文的稳定 checkpoint key。"""
    value = json.dumps({key: item[key] for key in ("seed", "experiment_group", "dataset", "task_id")}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def run_batch(root: Path, spec: dict[str, Any], output_root: Path, backend_name: str, freeze_git_sha: str | None, *, dry_run: bool = False, resume: bool = False) -> dict[str, Any]:
    """执行或 dry-run 全部 240 条任务，逐条失败并更新 checkpoint。"""
    items = plan(spec)
    if not dry_run and freeze_git_sha is None:
        raise ValueError("formal execution requires freeze_git_sha")
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_root / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8")) if resume and checkpoint_path.exists() else {"result_scope": spec["result_scope"], "freeze_git_sha": freeze_git_sha, "planned": len(items), "completed": {}}
    if dry_run:
        return {"planned": len(items), "completed": len(checkpoint.get("completed", {})), "dry_run": True, "result_scope": spec["result_scope"]}
    results = checkpoint.setdefault("completed", {})
    for item in items:
        key = task_key(item)
        if key in results:
            continue
        try:
            record = execute_item(root, spec, item, output_root, backend_name)
            results[key] = {"status": "completed", "task_success": bool(record.get("task_success"))}
        except Exception as error:
            results[key] = {"status": "infrastructure_failure", "error_category": type(error).__name__}
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"planned": len(items), "completed": len(results), "dry_run": False, "result_scope": spec["result_scope"]}
