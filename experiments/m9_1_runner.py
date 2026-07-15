"""M9.1 独立 Runner 的计划和 S1-S4 语义，不复用 M9 G1-G4 配置。"""

from __future__ import annotations

from typing import Any
import json
import hashlib
from pathlib import Path
import sys
import time

from protocol.compact_v2 import CompactProtocolV2
from state.vector_v2 import StateVectorV2
from memory.gated_shared_memory_v2 import GatedSharedMemoryV2


GROUPS = ("S1", "S2", "S3", "S4")

METRIC_FIELDS = (
    "agent_message_count", "agent_text_message_count", "agent_protocol_message_count",
    "agent_text_characters", "agent_text_tokens", "protocol_payload_bytes",
    "protocol_payload_tokens", "protocol_header_bytes", "capability_handshake_count",
    "capability_handshake_bytes", "reference_id_count", "repeated_context_bytes",
    "deduplicated_context_bytes", "prompt_tokens", "completion_tokens", "total_tokens",
    "request_count", "provider_latency_seconds", "state_vector_count", "state_vector_bytes",
    "state_reference_bytes", "equivalent_text_state_bytes", "state_compression_ratio",
    "state_encode_latency", "state_decode_latency", "invalid_state_count", "memory_query_count",
    "memory_candidate_count", "memory_hit_count", "memory_accept_count", "memory_reject_count",
    "memory_abstain_count", "memory_reuse_count", "memory_injected_count", "memory_injected_tokens",
    "memory_injected_bytes", "memory_write_count", "memory_success_write_count",
    "memory_eviction_count", "memory_hit_rate", "memory_accept_rate",
    "memory_effective_reuse_rate", "sandbox_completion_rate", "total_wall_time",
    "model_quality_failure",
)


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


def metric_defaults() -> dict[str, str]:
    """返回不能从单条公开记录可靠恢复时使用的统一 unavailable 标记。"""
    return {field: "unavailable" for field in METRIC_FIELDS}


def _protocol_session() -> dict[str, Any]:
    """创建一个连续任务组共享的 V2 协议会话，并缓存唯一握手。"""
    endpoint = CompactProtocolV2()
    capability_id = endpoint.register_capability("executor", "执行公开候选生成动作", ("generate",))
    return {"endpoint": endpoint, "capability_id": capability_id, "pending_handshake": endpoint.begin_sequence(("compact_protocol_v2",))}


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


def _record_path(output_root: Path, item: dict[str, Any]) -> Path:
    """返回不含任务原文且跨平台稳定的公开记录路径。"""
    task_id = item["task_id"].replace(":", "_").replace("/", "_")
    return output_root / f"{item['plan_index']:03d}_{item['experiment_group']}_{item['dataset']}_{task_id}.json"


def _write_public_record(output_root: Path, item: dict[str, Any], record: dict[str, Any]) -> None:
    """以 UTF-8 原子语义写入单条公开结果，不写入候选代码或私有评测内容。"""
    output_root.mkdir(parents=True, exist_ok=True)
    record_path = _record_path(output_root, item)
    temporary_path = record_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(record_path)


def _failure_record(spec: dict[str, Any], item: dict[str, Any], backend_name: str, freeze_git_sha: str | None, error: Exception) -> dict[str, Any]:
    """将单任务基础设施异常脱敏为可验证的最终公开记录。"""
    return {
        "schema_version": "1.0", **item, **group_config(item["experiment_group"]), **metric_defaults(),
        "result_scope": spec["result_scope"], "freeze_git_sha": freeze_git_sha,
        "implementation_git_sha": spec["implementation_git_sha"], "backend": backend_name,
        "model": spec["model"], "task_success": False,
        "final_status": "failed_infrastructure", "infrastructure_failure": True,
        # 只保留异常类别，避免将路径、请求或私有回溯写入公开结果。
        "error_category": type(error).__name__, "public_leakage_count": 0,
    }


def execute_item(root: Path, spec: dict[str, Any], item: dict[str, Any], output_root: Path, backend_name: str, *, freeze_git_sha: str | None = None, result_scope: str = "m9_1_real_canary", memory: GatedSharedMemoryV2 | None = None, protocol_session: dict[str, Any] | None = None) -> dict[str, Any]:
    """执行一项固定 M9.1 canary，使用真实 Backend 时只写公开结果。"""
    if backend_name not in {"mock", "openai_compatible"}:
        raise ValueError("unsupported canary backend")
    from generation.candidate_parser import parse_candidate
    from llm.config import LLMConfig, create_backend
    from llm.models import LLMMessage, LLMRequest
    from experiments.m9_runner import DATA
    from runtime.real_llm_runner import approved_tasks
    from sandbox.private_eval import evaluate_private

    started = time.perf_counter()
    group, dataset = item["experiment_group"], item["dataset"]
    selection, data_path = (root / value for value in DATA[dataset])
    task = next(value for value in approved_tasks(selection, data_path, 0) + approved_tasks(selection, data_path, 1) if value.task_id == item["task_id"])
    public_fields = {"task_id": task.task_id, "function_name": task.function_name, "signature": task.signature, "description": task.task_description}
    system = "You are a Python benchmark solver. Return code only."
    text = f"Implement this Python function. Return code only.\nFunction: {task.function_name}\nSignature: {task.signature}\nDescription: {task.task_description}"
    state = StateVectorV2(phase="generation", source_role="planner", target_role="executor", progress_code=1, state_reference="sv_canary") if group in {"S3", "S4"} else None
    state_metrics = metric_defaults()
    if state is not None:
        # 编解码均在传递边界执行，保证只传递固定 bytes 而不附加完整状态文本。
        encode_started = time.perf_counter()
        encoded_state = state.encode()
        decode_started = time.perf_counter()
        StateVectorV2.decode(encoded_state)
        state_metrics.update({
            "state_vector_count": 1,
            "state_vector_bytes": len(encoded_state),
            "state_reference_bytes": len(state.state_reference.encode("ascii")),
            "equivalent_text_state_bytes": state.equivalent_text_state_bytes(),
            "state_compression_ratio": state.compression_ratio(),
            "state_encode_latency": decode_started - encode_started,
            "state_decode_latency": time.perf_counter() - decode_started,
            "invalid_state_count": 0,
        })
    if group == "S4" and memory is None:
        # Canary 独立执行时创建本地 scope；批量执行会显式传入组级实例。
        memory = GatedSharedMemoryV2(dataset=dataset, task_group=task.group_id, seed=item["seed"], experiment_id=spec["experiment_id"])
    memory_records = memory.retrieve(task_id=task.task_id, topic=task.task_description, tags=(task.group_id,), task_type="candidate_generation") if memory else []
    protocol_metrics = metric_defaults()
    if group == "S1":
        prompt = text
        protocol_metrics.update({
            "agent_message_count": 1, "agent_text_message_count": 1,
            "agent_protocol_message_count": 0, "agent_text_characters": len(text),
        })
    else:
        session = protocol_session if protocol_session is not None else _protocol_session()
        endpoint = session["endpoint"]
        capability_id = session["capability_id"]
        before = endpoint.metrics.as_dict()
        handshake = session.pop("pending_handshake", None)
        task_ref_payload = endpoint.encode_task_registration(public_fields)
        task_ref = endpoint.references.register("task", public_fields)
        prompt_payload = endpoint.encode_action(action="generate", sender="Planner", receiver="Executor", capability_id=capability_id, task_ref=task_ref, inputs={"state_vector_id": "sv_canary" if state else None, "memory_ids": [record.memory_id for record in memory_records]})
        # 任务注册和动作引用共同构成对 Executor 的公开通信；任务说明不以额外自然语言重复注入。
        messages = ([handshake] if handshake is not None else []) + [task_ref_payload, prompt_payload]
        prompt = "Use these structured public protocol messages and return code only.\n" + "\n".join(payload.decode("utf-8") for payload in messages)
        values = endpoint.metrics.as_dict()
        protocol_metrics.update({
            "agent_message_count": len(messages), "agent_text_message_count": 0,
            "agent_protocol_message_count": len(messages),
            **{key: values[key] - before[key] for key in values},
        })
    backend = create_backend(LLMConfig.from_env()) if backend_name == "openai_compatible" else create_backend(LLMConfig(backend="mock"))
    response = backend.generate(LLMRequest((LLMMessage("system", system), LLMMessage("user", prompt)), backend.model, temperature=0, max_tokens=spec["generation_parameters"]["max_tokens"], seed=item["seed"]))
    artifact = parse_candidate(response.text, task.function_name)
    private = {value["task_id"]: value for value in map(json.loads, data_path.read_text(encoding="utf-8").splitlines())}[task.task_id]
    evaluation = evaluate_private(private, artifact["candidate_code"]) if artifact["parse_status"] == "success" else {"task_success": False, "official_test_count": 0, "official_test_pass_count": 0}
    memory_metrics = metric_defaults()
    if memory:
        for memory_record in memory_records:
            memory.reuse(memory_record.memory_id, task_id=task.task_id, task_success=bool(evaluation["task_success"]))
        memory.write(source_agent="Summarizer", created_at="canary", task_topic=task.task_description, summary="公开策略摘要", tags=(task.group_id,), task_type="candidate_generation", provenance="canary", confidence=1.0, success_status="success" if evaluation["task_success"] else "failure", source_task_id=task.task_id)
        memory_values = memory.metrics.as_dict()
        memory_metrics.update(memory_values)
        memory_metrics["memory_injected_bytes"] = sum(len(record.summary.encode("utf-8")) for record in memory_records)
    success = bool(evaluation["task_success"])
    model_metrics = metric_defaults()
    model_metrics.update({
        "prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens, "request_count": 1,
        "provider_latency_seconds": response.latency_seconds, "sandbox_completion_rate": 1.0,
        "total_wall_time": time.perf_counter() - started, "model_quality_failure": not success,
    })
    record = {"schema_version": "1.0", **item, **group_config(group), **metric_defaults(), **protocol_metrics, **state_metrics, **memory_metrics, **model_metrics, "result_scope": result_scope, "freeze_git_sha": freeze_git_sha, "implementation_git_sha": spec["implementation_git_sha"], "backend": backend_name, "model": spec["model"], "parse_status": artifact["parse_status"], "candidate_sha256": artifact.get("candidate_sha256"), "task_success": success, "final_status": "completed_success" if success else "failed_official_tests", "official_test_count": evaluation.get("official_test_count"), "official_test_pass_count": evaluation.get("official_test_pass_count"), "latency_seconds": response.latency_seconds, "public_leakage_count": 0}
    _write_public_record(output_root, item, record)
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
    public_tasks = output_root / "public" / "tasks"
    memories: dict[tuple[str, str, int, str], GatedSharedMemoryV2] = {}
    protocols: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for item in items:
        key = task_key(item)
        if key in results:
            continue
        try:
            memory = None
            if item["experiment_group"] == "S4":
                memory_key = (item["dataset"], item["group_id"], item["seed"], spec["experiment_id"])
                memory = memories.setdefault(memory_key, GatedSharedMemoryV2(dataset=memory_key[0], task_group=memory_key[1], seed=memory_key[2], experiment_id=memory_key[3]))
            protocol_session = None
            if item["experiment_group"] != "S1":
                protocol_key = (item["dataset"], item["group_id"], item["seed"], item["experiment_group"])
                if protocol_key not in protocols:
                    protocols[protocol_key] = _protocol_session()
                protocol_session = protocols[protocol_key]
            record = execute_item(root, spec, item, public_tasks, backend_name, freeze_git_sha=freeze_git_sha, result_scope=spec["result_scope"], memory=memory, protocol_session=protocol_session)
            results[key] = {"status": "completed", "task_success": bool(record.get("task_success"))}
        except Exception as error:
            _write_public_record(public_tasks, item, _failure_record(spec, item, backend_name, freeze_git_sha, error))
            results[key] = {"status": "infrastructure_failure", "error_category": type(error).__name__}
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if len(results) == len(items) and all(_record_path(public_tasks, item).exists() for item in items):
        from experiments.m9_1_verifier import write_completion
        write_completion(output_root / "public", spec, freeze_git_sha)
    return {"planned": len(items), "completed": len(results), "dry_run": False, "result_scope": spec["result_scope"]}
