"""生成独立 M9.1 赛题对齐强化实验 Spec，不修改 M9 Spec。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import stable_hash


GROUP_MAP = {"G1": "S1", "G2": "S2", "G3": "S3", "G4": "S4"}


def build_spec(m9_spec: dict[str, Any], implementation_git_sha: str) -> dict[str, Any]:
    """从既有 M9 公开任务计划生成独立 M9.1 Spec。"""
    if m9_spec.get("task_plan_count") != 240 or len(m9_spec.get("task_plan", [])) != 240:
        raise ValueError("M9 task plan must contain 240 tasks")
    task_plan = [{**item, "experiment_group": GROUP_MAP[item["experiment_group"]]} for item in m9_spec["task_plan"]]
    identities = {(item["seed"], item["experiment_group"], item["dataset"], item["task_id"]) for item in task_plan}
    if len(identities) != 240:
        raise ValueError("M9.1 task plan is not unique")
    return {
        "schema_version": "1.0",
        "experiment_id": "m9_1_competition_alignment",
        "result_scope": "supplementary_competition_alignment_ablation",
        "conclusion_scope": "fixed_task_fixed_model_supplementary_analysis",
        "implementation_git_sha": implementation_git_sha,
        "source_m9_freeze_sha": "cc7aac0417afb6acab47baaf7449459692fa9444",
        "model": m9_spec["model"], "backend": m9_spec["backend"],
        "parser_version": m9_spec["parser_version"], "sandbox_version": m9_spec["sandbox_version"],
        "datasets": ["mbpp", "humaneval"], "seeds": [42, 43, 44],
        "experiment_groups": ["S1", "S2", "S3", "S4"],
        "group_configs": {
            "S1": {"mode": "text", "state_enabled": False, "memory_enabled": False, "component": "text_baseline"},
            "S2": {"mode": "protocol", "state_enabled": False, "memory_enabled": False, "component": "compact_protocol_v2"},
            "S3": {"mode": "protocol", "state_enabled": True, "memory_enabled": False, "component": "compact_protocol_v2+state_vector_v2"},
            "S4": {"mode": "protocol", "state_enabled": True, "memory_enabled": True, "component": "compact_protocol_v2+state_vector_v2+gated_shared_memory_v2"},
        },
        "generation_parameters": m9_spec["generation_parameters"],
        "component_versions": {
            "prompt": "candidate_codegen_v1", "parser": "candidate_parser_v1", "private_adapter": "private_adapter_v2",
            "sandbox": "private_subprocess_v1", "protocol": "compact_protocol_v2", "state_vector": "state_vector_v2", "shared_memory": "gated_shared_memory_v2",
        },
        "memory_config": {"backend": "gated_in_process_v2", "top_k": 3, "relevance_threshold": 0.5, "confidence_threshold": 0.5, "token_budget": 128, "scope": ["dataset", "task_group", "seed", "experiment_id"], "reset": "at_group_boundary"},
        "execution_order": {"seed_42": ["S1", "S2", "S3", "S4"], "seed_43": ["S2", "S3", "S4", "S1"], "seed_44": ["S3", "S4", "S1", "S2"], "within_group": ["mbpp", "humaneval"], "within_dataset": "manifest_order"},
        "task_plan_count": len(task_plan), "task_plan_sha256": stable_hash(task_plan), "task_plan": task_plan,
        "bootstrap": {"seed": 20260711, "resamples": 2000, "confidence": 0.95},
        "formal_acceptance": {"expected_final_records": 240, "expected_missing": 0, "expected_duplicates": 0, "public_leakage_scan": 0, "private_metrics": "available_or_explicit_unavailable_reason"},
        "preflight_gates": ["unit_tests", "windows_full_tests", "openEuler_full_tests", "fake_canary", "two_real_canaries", "public_leakage_zero", "implementation_freeze_sha", "run_on_freeze_sha"],
    }


def main() -> int:
    """生成 M9.1 Spec 文件。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--m9-spec", default=str(ROOT / "experiments/m9_experiment_spec.json"))
    parser.add_argument("--implementation-git-sha", required=True)
    parser.add_argument("--output", default=str(ROOT / "experiments/m9_1/spec.json"))
    args = parser.parse_args()
    spec = build_spec(json.loads(Path(args.m9_spec).read_text(encoding="utf-8")), args.implementation_git_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "task_plan_count": spec["task_plan_count"], "task_plan_sha256": spec["task_plan_sha256"], "result_scope": spec["result_scope"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
