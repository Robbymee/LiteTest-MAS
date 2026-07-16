from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution",
    "reference_solution", "official_tests", "expected_output", "private_traceback",
    "api_key", "authorization", "request_ids",
}
SAFE_FIELDS = {
    "experiment_group", "dataset", "group_id", "seed", "record_count", "task_count",
    "task_success", "task_success_rate", "official_test_pass_rate", "parse_success_rate",
    "sandbox_completion_rate", "agent_message_count", "agent_text_message_count",
    "agent_protocol_message_count", "agent_text_characters", "agent_text_tokens",
    "protocol_payload_bytes", "protocol_payload_tokens", "protocol_header_bytes",
    "capability_handshake_count", "capability_handshake_bytes", "reference_id_count",
    "repeated_context_bytes", "deduplicated_context_bytes", "prompt_tokens",
    "completion_tokens", "total_tokens", "provider_latency_seconds", "total_wall_time",
    "state_vector_count", "state_vector_bytes", "equivalent_text_state_bytes",
    "state_compression_ratio", "state_encode_latency", "state_decode_latency",
    "memory_query_count", "memory_candidate_count", "memory_hit_count",
    "memory_accept_count", "memory_reject_count", "memory_abstain_count",
    "memory_reuse_count", "memory_injected_tokens", "memory_injected_bytes",
    "memory_hit_rate", "memory_accept_rate", "memory_effective_reuse_rate",
    "infrastructure_failure", "model_quality_failure",
}


def recursive_keys(value: Any) -> set[str]:
    """递归返回结构化公开数据中的全部字段名。"""
    if isinstance(value, dict):
        return set(value).union(*(recursive_keys(child) for child in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(recursive_keys(child) for child in value)) if value else set()
    return set()


def _read_json(path: Path) -> Any:
    value = json.loads(path.read_text(encoding="utf-8"))
    forbidden = FORBIDDEN & recursive_keys(value)
    if forbidden:
        raise ValueError("forbidden_public_field:" + ",".join(sorted(forbidden)))
    return value


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        forbidden = FORBIDDEN & set(reader.fieldnames or ())
        if forbidden:
            raise ValueError("forbidden_public_field:" + ",".join(sorted(forbidden)))
        return [{key: row[key] for key in SAFE_FIELDS if key in row} for row in reader]


def _safe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in SAFE_FIELDS if key in row} for row in rows]


def build_data(m9_dir: Path, m9_1_dir: Path, output_dir: Path) -> dict[str, Any]:
    """从公开聚合产物构建赛事 Dashboard 的统一数据文件。"""
    m9_manifest = _read_json(m9_dir / "analysis_manifest.json")
    m9_1_manifest = _read_json(m9_1_dir / "m9_1_aggregate_manifest.json")
    for name, manifest in (("M9", m9_manifest), ("M9.1", m9_1_manifest)):
        if manifest.get("final_record_count") != 240 or manifest.get("strict_verifier", {}).get("valid") is not True:
            raise ValueError(f"invalid_public_manifest:{name}")

    data = {
        "schema_version": "1.0",
        "experiments": {
            "m9": {
                "label": "M9 正式实验", "manifest": m9_manifest,
                "groups": _read_csv(m9_dir / "quality_cost_tradeoff.csv"),
                "datasets": _read_csv(m9_dir / "dataset_group_summary.csv"),
                "task_groups": _read_csv(m9_dir / "dataset_group_summary.csv"),
                "seeds": _read_csv(m9_dir / "seed_consistency_summary.csv"),
            },
            "m9_1": {
                "label": "M9.1 赛题对齐补充实验", "manifest": m9_1_manifest,
                "groups": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_groups.json")),
                "datasets": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_datasets.json")),
                "task_groups": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_task_groups.json")),
                "seeds": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_seeds.json")),
            },
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "data.json"
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"data_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "experiment_count": 2}


def main() -> int:
    """执行赛事 Dashboard 公开数据构建命令。"""
    parser = argparse.ArgumentParser(description="构建中文赛事 Dashboard 的公开数据")
    parser.add_argument("--m9-dir", required=True)
    parser.add_argument("--m9-1-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        result = build_data(Path(args.m9_dir), Path(args.m9_1_dir), Path(args.output_dir))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"赛事 Dashboard 数据构建失败：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
