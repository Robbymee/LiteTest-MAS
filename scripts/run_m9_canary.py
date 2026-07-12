from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import canary_item, resume_or_execute, stable_hash
from llm.config import LLMConfig, create_backend
from llm.mock_backend import MockLLMBackend


def implementation_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def canary_spec(backend, model):
    return {
        "schema_version": "1.0", "experiment_id": "m9_p3_canary", "result_scope": "m9_runner_canary",
        "conclusion_scope": "runner_integration_validation_only", "implementation_git_sha": implementation_sha(),
        "model": model, "backend": backend, "generation_parameters": {"temperature": 0, "max_tokens": 256, "seed": 42},
        "parser_version": "candidate_parser_v1", "sandbox_version": "private_subprocess_v1",
    }


def main():
    parser = argparse.ArgumentParser(description="Run one fixed M9 P3 canary without creating a formal experiment record.")
    parser.add_argument("--canary", required=True, choices=["mbpp_g1", "humaneval_g4"])
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--backend", choices=["mock", "openai_compatible"], required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    item = canary_item(ROOT, args.canary)
    config = LLMConfig.from_env()
    if args.backend == "openai_compatible":
        if config.backend != "openai_compatible":
            raise SystemExit("openai_compatible canary requires LLM_BACKEND=openai_compatible")
        backend = create_backend(config)
        model = config.model
    else:
        from runtime.real_llm_runner import approved_tasks
        selection, task_file = (ROOT / value for value in {"mbpp": ("datasets/manifests/mbpp_selected_groups.json", "datasets/processed/mbpp/mbpp_tasks.jsonl"), "humaneval": ("datasets/manifests/humaneval_selected_groups.json", "datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl")}[item["dataset"]])
        task = next(task for task in approved_tasks(selection, task_file, 0) + approved_tasks(selection, task_file, 1) if task.task_id == item["task_id"])
        backend = MockLLMBackend("mock-m9-canary-v1", fixed_response=f"```python\ndef {task.function_name}(*args, **kwargs):\n    return None\n```")
        model = backend.model
    spec = canary_spec(args.backend, model)
    record, resumed_skip = resume_or_execute(ROOT, item, args.output_root, backend, spec, "not-a-freeze", [item], resume=args.resume, write_completion_marker=False)
    print(json.dumps({"canary": args.canary, "final_status": record["final_status"], "parse_status": record["parse_status"], "resumed_skip": resumed_skip, "result_scope": record["result_scope"], "canary_spec_sha256": stable_hash(spec)}, sort_keys=True))


if __name__ == "__main__":
    main()
