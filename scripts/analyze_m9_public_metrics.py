"""基于 M9 公共记录生成赛题指标补充分析，不读取私有工件。"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.aggregate_m9_results import read_public_tasks
from scripts.verify_m9_run import verify


UNAVAILABLE = "unavailable"
UNAVAILABLE_REASON = "既有 M9 公共记录未记录该字段，不能从其他指标反推。"


def unavailable(reason: str = UNAVAILABLE_REASON) -> dict[str, str]:
    """构造稳定的不可恢复指标表示，避免将缺失数据误写为零。"""
    return {"value": UNAVAILABLE, "availability": UNAVAILABLE, "reason": reason}


def available(value: int | float | str | bool | None) -> dict[str, Any]:
    """构造已由公共记录直接提供或可精确派生的指标表示。"""
    return {"value": value, "availability": "available", "reason": ""}


def mean_value(records: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    """计算公共数值字段均值；任一缺失值会保留为不可恢复。"""
    values = [record.get(field) for record in records]
    if not values or any(value is None for value in values):
        return unavailable()
    return available(mean(float(value) for value in values))


def rate(numerator: int, denominator: int) -> dict[str, Any]:
    """计算有明确计数来源的比率，分母为零时不伪造数值。"""
    if denominator == 0:
        return unavailable("该分母在公共记录中为零，无法定义比率。")
    return available(numerator / denominator)


def flatten(row: dict[str, Any]) -> dict[str, Any]:
    """将带可用性元数据的指标转换为稳定 CSV 行。"""
    output: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, dict) and {"value", "availability", "reason"} <= set(value):
            output[key] = value["value"]
            output[f"{key}_availability"] = value["availability"]
            output[f"{key}_reason"] = value["reason"]
        else:
            output[key] = value
    return output


def _communication_summary(records: list[dict[str, Any]], dimensions: dict[str, Any]) -> dict[str, Any]:
    return {
        **dimensions,
        "record_count": len(records),
        "agent_message_count": mean_value(records, "message_count"),
        "agent_text_message_count": unavailable(),
        "agent_protocol_message_count": unavailable(),
        "agent_text_characters": mean_value(records, "text_character_count"),
        "agent_text_tokens": unavailable(),
        "protocol_payload_bytes": unavailable(),
        "protocol_payload_tokens": unavailable(),
        "protocol_header_bytes": unavailable(),
        "capability_handshake_count": unavailable(),
        "capability_handshake_bytes": unavailable(),
        "reference_id_count": unavailable(),
        "repeated_context_bytes": unavailable(),
        "deduplicated_context_bytes": unavailable(),
        "prompt_tokens": mean_value(records, "prompt_tokens"),
        "completion_tokens": mean_value(records, "completion_tokens"),
        "total_tokens": mean_value(records, "total_tokens"),
        "request_count": mean_value(records, "request_count"),
        "provider_latency_seconds": mean_value(records, "latency_seconds"),
    }


def _state_summary(records: list[dict[str, Any]], dimensions: dict[str, Any]) -> dict[str, Any]:
    return {
        **dimensions,
        "record_count": len(records),
        "state_vector_count": mean_value(records, "state_vector_count"),
        "state_vector_bytes": mean_value(records, "state_vector_bytes"),
        "state_reference_bytes": unavailable(),
        "equivalent_text_state_bytes": unavailable(),
        "state_compression_ratio": unavailable("缺少 equivalent_text_state_bytes，不能计算压缩率。"),
        "state_encode_latency": unavailable(),
        "state_decode_latency": unavailable(),
        "invalid_state_count": unavailable(),
    }


def _quality_summary(records: list[dict[str, Any]], dimensions: dict[str, Any]) -> dict[str, Any]:
    official_count = sum(int(record["official_test_count"]) for record in records)
    official_pass = sum(int(record["official_test_pass_count"]) for record in records)
    return {
        **dimensions,
        "record_count": len(records),
        "task_success": available(mean(float(bool(record["task_success"])) for record in records)),
        "official_test_pass_rate": rate(official_pass, official_count),
        "parse_success_rate": available(mean(float(record["parse_status"] == "success") for record in records)),
        "sandbox_completion_rate": available(mean(float(bool(record["sandbox_completed"])) for record in records)),
        "total_wall_time": unavailable(),
        "infrastructure_failure": available(sum(bool(record["infrastructure_failure"]) for record in records)),
        "model_quality_failure": available(sum(bool(record["model_quality_failure"]) for record in records)),
    }


def analyze_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """从公共任务记录构造通信、状态、记忆、质量的补充分析表。"""
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_dataset_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_seed_group: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_group[str(record["experiment_group"])].append(record)
        by_dataset_group[(str(record["dataset"]), str(record["experiment_group"]))].append(record)
        by_seed_group[(int(record["seed"]), str(record["experiment_group"]))].append(record)

    communication = [flatten(_communication_summary(rows, {"experiment_group": group})) for group, rows in sorted(by_group.items())]
    state = [flatten(_state_summary(rows, {"experiment_group": group})) for group, rows in sorted(by_group.items())]
    dataset_group = []
    quality_cost = []
    for (dataset, group), rows in sorted(by_dataset_group.items()):
        communication_row = _communication_summary(rows, {"dataset": dataset, "experiment_group": group})
        state_row = _state_summary(rows, {"dataset": dataset, "experiment_group": group})
        quality_row = _quality_summary(rows, {"dataset": dataset, "experiment_group": group})
        dataset_group.append(flatten({**communication_row, **state_row, **quality_row}))
    for group, rows in sorted(by_group.items()):
        quality_cost.append(flatten({**_communication_summary(rows, {"experiment_group": group}), **_quality_summary(rows, {"experiment_group": group})}))

    seed = [flatten({**_communication_summary(rows, {"seed": seed_value, "experiment_group": group}), **_quality_summary(rows, {"seed": seed_value, "experiment_group": group})}) for (seed_value, group), rows in sorted(by_seed_group.items())]
    memory = []
    for record in sorted(records, key=lambda value: (value["dataset"], value["seed"], value["experiment_group"], value["plan_index"])):
        if record["experiment_group"] != "G4":
            continue
        references = record.get("memory_reference_ids") or []
        memory.append(flatten({
            "dataset": record["dataset"], "group_id": record["group_id"], "task_id": record["task_id"], "seed": record["seed"],
            "memory_query_count": available(record["memory_read_count"]),
            "memory_candidate_count": unavailable(),
            "memory_hit_count": available(record["memory_hit_count"]),
            "memory_accept_count": unavailable(),
            "memory_reject_count": unavailable(),
            "memory_reuse_count": available(record["memory_reuse_count"]),
            "memory_injected_count": unavailable(),
            "memory_injected_tokens": unavailable(),
            "memory_injected_bytes": unavailable(),
            "memory_write_count": available(record["memory_write_count"]),
            "memory_success_write_count": unavailable(),
            "memory_eviction_count": unavailable(),
            "memory_hit_rate": rate(int(record["memory_hit_count"]), int(record["memory_read_count"])),
            "memory_accept_rate": unavailable(),
            "memory_effective_reuse_rate": unavailable("公开记录没有逐条引用后的可评测关联。"),
            "memory_reference_id_count": available(len(references)),
            "task_success": available(bool(record["task_success"])),
        }))
    return {
        "communication_layer_summary": communication,
        "state_efficiency_summary": state,
        "memory_reuse_detail": memory,
        "dataset_group_summary": dataset_group,
        "seed_consistency_summary": seed,
        "quality_cost_tradeoff": quality_cost,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """以 UTF-8 写入稳定字段的 CSV，即使没有行也保留文件。"""
    fields = sorted({field for row in rows for field in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, artifacts: dict[str, list[dict[str, Any]]], manifest: dict[str, Any]) -> None:
    """写入中文公开指标说明，不把缺失指标解释为实验结论。"""
    groups = artifacts["quality_cost_tradeoff"]
    lines = [
        "# M9 赛题指标补充分析", "",
        "## 数据边界", "",
        "本报告只读取已经通过 strict verifier 的 M9 `public/tasks` 记录。它不读取 private attempts、candidate code、raw response、hidden tests 或模型服务。",
        f"- freeze SHA：`{manifest['freeze_git_sha']}`",
        f"- final records：`{manifest['final_record_count']}`",
        f"- strict verifier：`passed`",
        "", "## 指标可用性", "",
        "`message_count`、`text_character_count`、模型 Prompt/Completion/Total Token、请求次数、provider latency、StateVector 次数和字节、以及 V1 Memory 的 read/hit/reuse/write 计数可以直接从公共记录恢复。",
        "握手、能力发现、通信 Token、Protocol payload/header bytes、重复上下文、等价文本状态、状态编解码耗时、Memory accept/reject/abstain/injection 与有效复用关联均为 `unavailable`；缺失不等于零。",
        "", "## 质量与成本概览", "",
        "| 组别 | 任务成功率 | official-test 通过率 | 总模型 Token | provider latency | 通信字符 | StateVector 字节 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in groups:
        lines.append("| {group} | {success} | {official} | {tokens} | {latency} | {characters} | {state} |".format(
            group=row["experiment_group"], success=row["task_success"], official=row["official_test_pass_rate"],
            tokens=row["total_tokens"], latency=row["provider_latency_seconds"],
            characters=row["agent_text_characters"], state=row.get("state_vector_bytes", UNAVAILABLE),
        ))
    lines.extend([
        "", "## 解释限制", "",
        "M9 可以说明 Protocol V1 的质量、总模型 Token 和 provider latency 的观察差异，但不能据此证明 Agent 间通信更省。StateVector V1 的字节数不能单独证明替代重复文本。Memory reuse 只表示引用事件，不能解释为因果质量提升；G4 相对 G3 的负向任务成功差异继续保留。",
        "", "详细逐组、逐数据集、逐 seed 和逐任务的公共指标见同目录 CSV。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(run_root: Path, spec_path: Path, output_dir: Path, expected_freeze_sha: str, plan_root: Path) -> dict[str, Any]:
    """严格验证 M9 后生成独立补充分析，不修改原聚合或运行目录。"""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    strict = verify(run_root, spec, root=plan_root, strict=True, expected_freeze_sha=expected_freeze_sha)
    if not strict["valid"]:
        raise ValueError("strict_verifier_failed:" + ",".join(strict["errors"]))
    records = read_public_tasks(run_root)
    artifacts = analyze_records(records)
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, rows in artifacts.items():
        write_csv(output_dir / f"{name}.csv", rows)
    manifest = {"freeze_git_sha": expected_freeze_sha, "final_record_count": len(records)}
    write_report(output_dir / "赛题指标补充分析.md", artifacts, manifest)
    (output_dir / "analysis_manifest.json").write_text(json.dumps({"schema_version": "1.0", **manifest, "strict_verifier": {"valid": True}}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-freeze-sha", required=True)
    parser.add_argument("--plan-root", default=str(ROOT))
    args = parser.parse_args()
    try:
        print(json.dumps(run_analysis(Path(args.run_root), Path(args.spec), Path(args.output_dir), args.expected_freeze_sha, Path(args.plan_root)), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"M9 公共指标分析失败: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
