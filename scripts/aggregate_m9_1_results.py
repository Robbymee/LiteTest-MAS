"""聚合 M9.1 的公开 final records，不读取私有评测产物。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from experiments.m9_1_verifier import FORBIDDEN, verify


ROOT = Path(__file__).resolve().parents[1]
UNAVAILABLE = "unavailable"
COMPARISONS = (("S2", "S1"), ("S3", "S2"), ("S4", "S3"), ("S4", "S1"))
QUALITY_METRICS = ("task_success", "official_test_pass_rate", "parse_success_rate", "sandbox_completion_rate")


def canonical(value: Any) -> str:
    """使用跨平台稳定 JSON 序列化公开聚合输入或输出。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_public_tasks(run_root: Path) -> list[dict[str, Any]]:
    """仅读取公开任务记录，并在聚合前拒绝私有字段。"""
    paths = sorted((run_root / "public" / "tasks").glob("*.json"))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    for record in records:
        forbidden = FORBIDDEN & set(record)
        if forbidden:
            raise ValueError("forbidden_public_field:" + ",".join(sorted(forbidden)))
    return records


def numeric_values(records: Iterable[dict[str, Any]], field: str) -> list[float] | None:
    """返回可恢复数值；任一 unavailable 表示该聚合字段不可用。"""
    values: list[float] = []
    for record in records:
        value = record.get(field)
        if value in (None, UNAVAILABLE):
            return None
        if isinstance(value, bool):
            values.append(float(value))
        elif isinstance(value, (int, float)):
            values.append(float(value))
        else:
            return None
    return values


def average(records: list[dict[str, Any]], field: str) -> float | str:
    """计算可恢复字段均值，缺失时显式保留 unavailable。"""
    values = numeric_values(records, field)
    return mean(values) if values is not None and values else UNAVAILABLE


def rate(records: list[dict[str, Any]], numerator: str, denominator: str) -> float | str:
    """计算公开计数字段的比率，避免以零或缺失值替代未知信息。"""
    numerators = numeric_values(records, numerator)
    denominators = numeric_values(records, denominator)
    if numerators is None or denominators is None:
        return UNAVAILABLE
    total = sum(denominators)
    return sum(numerators) / total if total else UNAVAILABLE


def summarize(records: list[dict[str, Any]], dimensions: dict[str, Any]) -> dict[str, Any]:
    """汇总一组公开记录，稳定保留质量、通信、状态与记忆指标。"""
    row = {**dimensions, "record_count": len(records)}
    for field in (
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
        "memory_injected_bytes", "memory_write_count", "memory_success_write_count", "memory_eviction_count",
        "memory_hit_rate", "memory_accept_rate", "memory_effective_reuse_rate", "total_wall_time",
        "model_quality_failure",
    ):
        row[field] = average(records, field)
    row["task_success"] = average(records, "task_success")
    row["official_test_pass_rate"] = rate(records, "official_test_pass_count", "official_test_count")
    row["parse_success_rate"] = mean(float(record.get("parse_status") == "success") for record in records)
    row["sandbox_completion_rate"] = average(records, "sandbox_completion_rate")
    row["infrastructure_failure"] = sum(record.get("final_status") == "failed_infrastructure" for record in records)
    return row


def bootstrap_mean_ci(deltas: list[float], *, resamples: int, confidence: float, seed: int) -> dict[str, float]:
    """以固定随机种子计算配对均值差的 percentile Bootstrap 区间。"""
    if not deltas:
        raise ValueError("empty_paired_deltas")
    generator = random.Random(seed)
    samples = sorted(
        mean(generator.choice(deltas) for _ in deltas)
        for _ in range(resamples)
    )
    lower_index = int(((1 - confidence) / 2) * resamples)
    upper_index = min(resamples - 1, int(((1 + confidence) / 2) * resamples))
    return {"mean_difference": mean(deltas), "ci_lower": samples[lower_index], "ci_upper": samples[upper_index]}


def paired_comparisons(records: list[dict[str, Any]], bootstrap: dict[str, Any]) -> list[dict[str, Any]]:
    """按 dataset、task_id、seed 配对 S 组，输出预注册比较的公开指标。"""
    indexed = {(row["experiment_group"], row["dataset"], row["task_id"], row["seed"]): row for row in records}
    rows: list[dict[str, Any]] = []
    for comparison_index, (treatment, control) in enumerate(COMPARISONS):
        keys = sorted({(row["dataset"], row["task_id"], row["seed"]) for row in records})
        for metric_index, metric in enumerate(QUALITY_METRICS):
            deltas: list[float] = []
            for dataset, task_id, seed_value in keys:
                treated, baseline = indexed.get((treatment, dataset, task_id, seed_value)), indexed.get((control, dataset, task_id, seed_value))
                if treated is None or baseline is None:
                    continue
                if metric == "official_test_pass_rate":
                    treated_value = rate([treated], "official_test_pass_count", "official_test_count")
                    baseline_value = rate([baseline], "official_test_pass_count", "official_test_count")
                elif metric == "parse_success_rate":
                    treated_value, baseline_value = float(treated.get("parse_status") == "success"), float(baseline.get("parse_status") == "success")
                else:
                    treated_value, baseline_value = treated.get(metric), baseline.get(metric)
                if isinstance(treated_value, (int, float, bool)) and isinstance(baseline_value, (int, float, bool)):
                    deltas.append(float(treated_value) - float(baseline_value))
            seed_material = f"{bootstrap['seed']}:{comparison_index}:{metric_index}".encode("utf-8")
            result = bootstrap_mean_ci(deltas, resamples=int(bootstrap["resamples"]), confidence=float(bootstrap["confidence"]), seed=int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big"))
            rows.append({"treatment_group": treatment, "control_group": control, "metric": metric, "paired_count": len(deltas), "bootstrap_seed": bootstrap["seed"], "bootstrap_resamples": bootstrap["resamples"], "confidence": bootstrap["confidence"], **result})
    return rows


def write_json(path: Path, value: Any) -> None:
    """以 UTF-8 写入可审计的公开 JSON 产物。"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """以 UTF-8 写入稳定字段的 CSV 公开汇总。"""
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, manifest: dict[str, Any], groups: list[dict[str, Any]]) -> None:
    """生成中文 M9.1 汇总说明，不把相关性写成因果结论。"""
    lines = [
        "# M9.1 公开结果聚合说明", "", "## 数据边界", "",
        "本报告只读取通过 Strict Verifier 的 `public/tasks` final records。它不读取 private tests、candidate code、raw response、私有 traceback 或模型服务。",
        f"- freeze SHA：`{manifest['freeze_git_sha']}`",
        f"- Spec SHA：`{manifest['spec_sha256']}`",
        f"- final records：`{manifest['final_record_count']}`", "", "## 组别概览", "",
        "| 组别 | 任务成功率 | official-test 通过率 | Agent 通信字符 | 总模型 Token | StateVector 字节 | Memory 注入 Token |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in groups:
        lines.append("| {experiment_group} | {task_success} | {official_test_pass_rate} | {agent_text_characters} | {total_tokens} | {state_vector_bytes} | {memory_injected_tokens} |".format(**row))
    lines.extend(["", "## 解释限制", "", "所有比较限于固定任务、固定模型和本次预注册配置。Memory 的有效复用表示引用后存在可评测结果，不可解释为因果质量提升；`unavailable` 表示记录没有可恢复值，不表示零。"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def aggregate(run_root: Path, spec_path: Path, output_dir: Path, freeze_git_sha: str) -> dict[str, Any]:
    """验证有效 M9.1 正式运行后生成独立、公开且可复核的聚合产物。"""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    strict = verify(run_root, spec, freeze_git_sha)
    if not strict["valid"]:
        raise ValueError("strict_verifier_failed:" + ",".join(strict["errors"]))
    records = read_public_tasks(run_root)
    if output_dir.exists():
        raise ValueError("output_dir_exists")
    output_dir.mkdir(parents=True)
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_group[record["experiment_group"]].append(record)
        by_dataset[record["dataset"]].append(record)
        by_task_group[(record["dataset"], record["group_id"])].append(record)
        by_seed[int(record["seed"])].append(record)
    groups = [summarize(rows, {"experiment_group": key}) for key, rows in sorted(by_group.items())]
    datasets = [summarize(rows, {"dataset": key}) for key, rows in sorted(by_dataset.items())]
    task_groups = [summarize(rows, {"dataset": key[0], "group_id": key[1]}) for key, rows in sorted(by_task_group.items())]
    seeds = [summarize(rows, {"seed": key}) for key, rows in sorted(by_seed.items())]
    comparisons = paired_comparisons(records, spec["bootstrap"])
    manifest = {"schema_version": "1.0", "result_scope": spec["result_scope"], "conclusion_scope": spec["conclusion_scope"], "freeze_git_sha": freeze_git_sha, "spec_sha256": hashlib.sha256(canonical(spec).encode("utf-8")).hexdigest(), "final_record_count": len(records), "strict_verifier": {"valid": True}, "bootstrap": spec["bootstrap"], "aggregate_input_sha256": hashlib.sha256(canonical(records).encode("utf-8")).hexdigest()}
    manifest["deterministic_aggregate_sha256"] = hashlib.sha256(canonical({"groups": groups, "datasets": datasets, "task_groups": task_groups, "seeds": seeds, "comparisons": comparisons}).encode("utf-8")).hexdigest()
    for name, rows in {"m9_1_aggregate_groups": groups, "m9_1_aggregate_datasets": datasets, "m9_1_aggregate_task_groups": task_groups, "m9_1_aggregate_seeds": seeds, "m9_1_paired_comparisons": comparisons}.items():
        write_json(output_dir / f"{name}.json", rows)
        write_csv(output_dir / f"{name}.csv", rows)
    write_json(output_dir / "m9_1_aggregate_manifest.json", manifest)
    write_report(output_dir / "M9.1公开结果聚合说明.md", manifest, groups)
    return manifest


def main() -> int:
    """提供公开 M9.1 聚合命令行入口。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--spec", default=str(ROOT / "experiments/m9_1/spec.json"))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--freeze-git-sha", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(aggregate(Path(args.run_root), Path(args.spec), Path(args.output_dir), args.freeze_git_sha), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"M9.1 公开结果聚合失败: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
