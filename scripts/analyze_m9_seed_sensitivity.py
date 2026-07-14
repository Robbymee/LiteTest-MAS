"""分析 M9 公开记录的跨 seed 重复性和按任务聚类的 Bootstrap 敏感性。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.aggregate_m9_results import COMPARISONS, METRICS, metric_value, read_public_tasks


UNAVAILABLE = "unavailable"


def percentile(values: list[float], probability: float) -> float:
    """计算已排序样本的线性插值分位数。"""
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def cluster_bootstrap_mean_ci(clusters: list[list[float]], *, resamples: int, confidence: float, seed: int) -> dict[str, float | int]:
    """以 dataset/task_id 为重采样单位计算均值差异的 Bootstrap 区间。"""
    if not clusters or any(not cluster for cluster in clusters):
        raise ValueError("empty_task_cluster")
    generator = random.Random(seed)
    count = len(clusters)
    samples = []
    for _ in range(resamples):
        sampled = [clusters[generator.randrange(count)] for _ in range(count)]
        values = [value for cluster in sampled for value in cluster]
        samples.append(mean(values))
    samples.sort()
    alpha = (1 - confidence) / 2
    values = [value for cluster in clusters for value in cluster]
    return {
        "cluster_count": count,
        "paired_count": len(values),
        "mean_difference": mean(values),
        "ci_lower": percentile(samples, alpha),
        "ci_upper": percentile(samples, 1 - alpha),
    }


def _all_equal(values: list[Any]) -> bool | str:
    """仅在三条 seed 记录完整时判断完全重复，避免把缺失误当不重复。"""
    if len(values) != 3 or any(value is None for value in values):
        return UNAVAILABLE
    return len(set(values)) == 1


def seed_consistency(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 dataset 和实验组统计同一任务三个 seed 的输出与指标重复比例。"""
    units: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        units[(record["experiment_group"], record["dataset"], record["group_id"], record["task_id"])].append(record)

    summaries: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for (experiment_group, dataset, _, _), rows in units.items():
        ordered = sorted(rows, key=lambda row: row["seed"])
        summaries[(experiment_group, dataset)].append(
            {
                "candidate_sha256": _all_equal([row.get("candidate_sha256") for row in ordered]),
                "task_success": _all_equal([bool(row["task_success"]) for row in ordered]),
                "official_test_pass_status": _all_equal(
                    [bool(row["official_test_pass_count"] == row["official_test_count"]) for row in ordered]
                ),
                "total_tokens": _all_equal([row.get("total_tokens") for row in ordered]),
            }
        )

    output = []
    for (experiment_group, dataset), rows in sorted(summaries.items()):
        result: dict[str, Any] = {"experiment_group": experiment_group, "dataset": dataset, "task_unit_count": len(rows)}
        for field in ("candidate_sha256", "task_success", "official_test_pass_status", "total_tokens"):
            values = [row[field] for row in rows]
            if any(value == UNAVAILABLE for value in values):
                result[f"{field}_all_seed_equal_rate"] = UNAVAILABLE
                result[f"{field}_availability"] = UNAVAILABLE
            else:
                result[f"{field}_all_seed_equal_rate"] = mean(float(value) for value in values)
                result[f"{field}_availability"] = "available"
        output.append(result)
    return output


def cluster_comparisons(records: list[dict[str, Any]], *, bootstrap_seed: int, resamples: int, confidence: float) -> list[dict[str, Any]]:
    """保留原比较方向，按 dataset/task_id 聚类重采样所有既有指标。"""
    by_group: dict[str, dict[tuple[int, str, str], dict[str, Any]]] = defaultdict(dict)
    for record in records:
        identity = (int(record["seed"]), str(record["dataset"]), str(record["task_id"]))
        by_group[str(record["experiment_group"])][identity] = record

    output = []
    for treatment, control in COMPARISONS:
        treatment_rows = by_group[treatment]
        control_rows = by_group[control]
        identities = sorted(set(treatment_rows) & set(control_rows))
        if len(identities) != len(treatment_rows) or len(identities) != len(control_rows):
            raise ValueError(f"unpaired_records:{treatment}_vs_{control}")
        for metric in METRICS:
            clusters: dict[tuple[str, str], list[float]] = defaultdict(list)
            for seed, dataset, task_id in identities:
                delta = metric_value(treatment_rows[(seed, dataset, task_id)], metric) - metric_value(control_rows[(seed, dataset, task_id)], metric)
                clusters[(dataset, task_id)].append(delta)
            result = cluster_bootstrap_mean_ci(list(clusters.values()), resamples=resamples, confidence=confidence, seed=bootstrap_seed)
            output.append(
                {
                    "treatment_group": treatment,
                    "control_group": control,
                    "metric": metric,
                    "difference_direction": "treatment_minus_control",
                    "bootstrap_seed": bootstrap_seed,
                    "bootstrap_resamples": resamples,
                    "confidence": confidence,
                    **result,
                }
            )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """使用 UTF-8 写入稳定的扁平 CSV。"""
    fields = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, consistency: list[dict[str, Any]], ordinary: list[dict[str, Any]], clustered: list[dict[str, Any]], *, bootstrap_seed: int, resamples: int) -> None:
    """写入中文敏感性报告，只比较公开普通与聚类 Bootstrap 结果。"""
    ordinary_success = {(row["treatment_group"], row["control_group"]): row for row in ordinary if row["metric"] == "task_success"}
    cluster_success = {(row["treatment_group"], row["control_group"]): row for row in clustered if row["metric"] == "task_success"}
    lines = [
        "# M9 随机种子相关性分析",
        "",
        "## 数据边界",
        "",
        "分析只读取 M9 `public/tasks` 与既有公开普通配对比较文件。candidate SHA 只用于计算重复比例，报告不输出 SHA 值、candidate 内容、private tests 或 raw responses。",
        "",
        "## 三个 seed 的重复比例",
        "",
        "| 实验组 | 数据集 | 任务单元数 | candidate SHA 完全重复率 | 任务成功状态完全重复率 | official-test 全通过状态完全重复率 | 总 Token 完全重复率 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in consistency:
        lines.append(
            "| {experiment_group} | {dataset} | {task_unit_count} | {candidate} | {success} | {official} | {tokens} |".format(
                experiment_group=row["experiment_group"], dataset=row["dataset"], task_unit_count=row["task_unit_count"],
                candidate=row["candidate_sha256_all_seed_equal_rate"], success=row["task_success_all_seed_equal_rate"],
                official=row["official_test_pass_status_all_seed_equal_rate"], tokens=row["total_tokens_all_seed_equal_rate"],
            )
        )
    lines.extend([
        "",
        "## Bootstrap 敏感性",
        "",
        f"普通配对 Bootstrap 保留既有结果。新增 task-cluster Bootstrap 以 `dataset + task_id` 为聚类单位，每个聚类包含 3 个 seed；固定 `bootstrap_seed={bootstrap_seed}`、`bootstrap_resamples={resamples}`、95% CI。",
        "",
        "| 比较 | 普通均值差 | 普通 95% CI | 聚类均值差 | 聚类 95% CI |",
        "| --- | ---: | --- | ---: | --- |",
    ])
    for treatment, control in COMPARISONS:
        normal = ordinary_success[(treatment, control)]
        cluster = cluster_success[(treatment, control)]
        lines.append(
            f"| {treatment}-{control} | {normal['mean_difference']:.4f} | [{normal['ci_lower']:.4f}, {normal['ci_upper']:.4f}] | {cluster['mean_difference']:.4f} | [{cluster['ci_lower']:.4f}, {cluster['ci_upper']:.4f}] |"
        )
    lines.extend([
        "",
        "## 解释限制",
        "",
        "temperature=0 并不保证不同 seed 的候选、成功状态或 Token 完全相同。重复比例描述本次固定任务和固定模型运行的相关性，不代表跨任务泛化。聚类 CI 将同一任务的三个 seed 作为一个重采样单元，反映 seed 内相关性可能对不确定性估计造成的影响；它不替换既有普通配对 CI。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(run_root: Path, ordinary_path: Path, output_dir: Path, *, bootstrap_seed: int = 20260711, resamples: int = 2000, confidence: float = 0.95) -> dict[str, int]:
    """读取公开任务并生成 P4 产物，不修改正式运行或既有普通聚合。"""
    records = read_public_tasks(run_root)
    ordinary = json.loads(ordinary_path.read_text(encoding="utf-8"))
    consistency = seed_consistency(records)
    clustered = cluster_comparisons(records, bootstrap_seed=bootstrap_seed, resamples=resamples, confidence=confidence)
    output_dir.mkdir(parents=True, exist_ok=False)
    write_csv(output_dir / "seed_correlation_summary.csv", consistency)
    write_csv(output_dir / "task_cluster_bootstrap.csv", clustered)
    write_report(output_dir / "随机种子相关性分析.md", consistency, ordinary, clustered, bootstrap_seed=bootstrap_seed, resamples=resamples)
    (output_dir / "seed_sensitivity_manifest.json").write_text(
        json.dumps({"schema_version": "1.0", "record_count": len(records), "bootstrap_seed": bootstrap_seed, "bootstrap_resamples": resamples}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"record_count": len(records), "comparison_count": len(clustered)}


def main() -> int:
    """提供 P4 只读分析 CLI。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--ordinary-comparisons", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=20260711)
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    args = parser.parse_args()
    print(json.dumps(run_analysis(args.run_root, args.ordinary_comparisons, args.output_dir, bootstrap_seed=args.bootstrap_seed, resamples=args.bootstrap_resamples), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
