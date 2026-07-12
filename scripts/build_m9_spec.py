from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import GROUPS, plan, stable_hash


def build_spec(implementation_git_sha: str) -> dict:
    items = plan(ROOT)
    if len(items) != 240 or len({(item["seed"], item["experiment_group"], item["dataset"], item["task_id"]) for item in items}) != 240:
        raise ValueError("the fixed plan must contain 240 unique tasks")
    return {
        "schema_version": "1.0",
        "experiment_id": "m9_formal_ablation_v1",
        "result_scope": "formal_real_llm_ablation",
        "conclusion_scope": "fixed_task_fixed_model_four_group_ablation",
        "implementation_git_sha": implementation_git_sha,
        "model": "local-llama31-8b-instruct",
        "backend": "openai_compatible",
        "parser_version": "candidate_parser_v1",
        "sandbox_version": "private_subprocess_v1",
        "datasets": ["mbpp", "humaneval"],
        "seeds": [42, 43, 44],
        "experiment_groups": ["G1", "G2", "G3", "G4"],
        "group_configs": {
            group: {"mode": "text" if group == "G1" else "protocol", "state_enabled": state, "memory_enabled": memory}
            for group, (state, memory) in GROUPS.items()
        },
        "generation_parameters": {
            "temperature": 0,
            "max_tokens": 256,
            "timeout_seconds": 300,
            "max_retries": 1,
            "retry": 1,
            "concurrency": 1,
            "stream": False,
        },
        "component_versions": {
            "prompt": "candidate_codegen_v1",
            "parser": "candidate_parser_v1",
            "private_adapter": "private_adapter_v2",
            "sandbox": "private_subprocess_v1",
            "state_vector": "state_vector_v1",
            "shared_memory": "shared_memory_fifo_v1",
        },
        "memory_config": {
            "backend": "in_process_fifo",
            "max_records": 32,
            "max_bytes": 8192,
            "scope": ["dataset", "experiment_group", "seed"],
            "reset": "at_group_boundary",
        },
        "execution_order": {
            "seed_42": ["G1", "G2", "G3", "G4"],
            "seed_43": ["G2", "G3", "G4", "G1"],
            "seed_44": ["G3", "G4", "G1", "G2"],
            "within_group": ["mbpp", "humaneval"],
            "within_dataset": "manifest_order",
        },
        "task_plan_count": len(items),
        "task_plan_sha256": stable_hash(items),
        "task_plan": items,
        "bootstrap": {"seed": 20260711, "resamples": 2000, "confidence": 0.95},
        "formal_acceptance": {
            "expected_final_records": 240,
            "expected_missing": 0,
            "expected_duplicates": 0,
            "public_leakage_scan": 0,
            "private_metrics": "available_or_explicit_unavailable_reason",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-git-sha", required=True)
    parser.add_argument("--output", default=str(ROOT / "experiments" / "m9_experiment_spec.json"))
    args = parser.parse_args()
    spec = build_spec(args.implementation_git_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"output": str(output), "task_plan_count": spec["task_plan_count"], "task_plan_sha256": spec["task_plan_sha256"], "implementation_git_sha": args.implementation_git_sha}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
