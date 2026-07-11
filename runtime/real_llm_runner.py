"""M5 real-LLM validation runner using only approved agent-visible task fields."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from llm.models import LLMMessage, LLMRequest
from runtime.sequence_runner import SelectedTask, SelectedTaskLoader, SequenceValidationError

RESULT_SCOPE = "real_llm_pilot"
CONCLUSION_SCOPE = "integration_and_runtime_validation_only"
BLOCKED_WORDS = {"hidden_reference_tests", "canonical_solution", "reference_solution", "official_tests", "challenge_tests", "contract", "api_key", "authorization"}

def safe_prompt(task: SelectedTask) -> str:
    view = task.agent_view("m5", 0, 0)
    serialized = json.dumps(view, ensure_ascii=False, sort_keys=True).lower()
    if any(word in serialized for word in BLOCKED_WORDS):
        raise SequenceValidationError("blocked field entered M5 prompt")
    return ("Create a concise, public test strategy for the following Python function. Do not assume hidden tests or a reference solution.\n"
            f"Task ID: {view['task_id']}\nFunction: {view['function_name']}\nSignature: {view['signature']}\nDescription: {view['task_description']}")

def run_tasks(tasks: list[SelectedTask], backend: Any, model: str, output_dir: Path, *, seed: int = 42, max_tokens: int = 256, memory=None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    records = []
    for index, task in enumerate(tasks, 1):
        record = {"dataset": task.task_id.split(":", 1)[0], "group_id": task.group_id, "task_id": task.task_id, "round_index": index, "mode": "text", "model": model, "backend": "openai_compatible", "result_scope": RESULT_SCOPE, "status": "failed", "request_id": None, "finish_reason": None, "prompt_tokens": None, "completion_tokens": None, "total_tokens": None, "usage_available": False, "latency_seconds": None, "retry_count": 0, "parse_result": "not_started", "error_type": None}
        try:
            prior = memory.read(task.group_id) if memory else []
            response = backend.generate(LLMRequest((LLMMessage("system", "You are a precise assistant."), LLMMessage("user", safe_prompt(task))), model, temperature=0, max_tokens=max_tokens, seed=seed))
            record.update({"status": "succeeded", "request_id": response.request_id, "finish_reason": response.finish_reason, "prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens, "usage_available": response.usage.usage_available, "latency_seconds": response.latency_seconds, "parse_result": "nonempty_response" if response.text.strip() else "empty_response"})
        except Exception as error:
            record.update({"error_type": getattr(error, "error_type", type(error).__name__), "parse_result": "backend_error"})
            if memory and record['status']=='succeeded': memory.write(source_task_id=task.source_task_id,source_round_index=index,category='public_test_strategy',key=task.group_id,safe_summary=f"Public strategy for {task.function_name}",tags=(task.group_id,))
        records.append(record)
    summary = {"result_scope": RESULT_SCOPE, "conclusion_scope": CONCLUSION_SCOPE, "planned_rounds": len(tasks), "executed_rounds": len(records), "succeeded_rounds": sum(r["status"] == "succeeded" for r in records), "failed_rounds": sum(r["status"] == "failed" for r in records), "skipped_rounds": 0, "memory": memory.trace() if memory else {"enabled":False}}
    (output_dir / "rounds.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary

def approved_tasks(selection: Path, tasks: Path, group_index: int, limit: int | None = None) -> list[SelectedTask]:
    manifest, selected = SelectedTaskLoader(selection, tasks).load()
    groups = manifest["groups"]
    if group_index < 0 or group_index >= len(groups): raise SequenceValidationError("group index is outside the fixed manifest")
    result = [task for task in selected if task.task_id in set(groups[group_index]["task_ids"])]
    return result[:limit] if limit is not None else result
