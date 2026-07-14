"""基于正式 M9 manifest 和公开聚合生成数据集、任务组分析。"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    """以 UTF-8 读取公开聚合 CSV，不访问运行目录或私有记录。"""
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def unique_task_plan(spec: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    """从正式 manifest 保留每个 dataset/group 的真实任务顺序。"""
    plan: dict[tuple[str, str], list[str]] = defaultdict(list)
    for item in spec["task_plan"]:
        key = (str(item["dataset"]), str(item["group_id"]))
        task_id = str(item["task_id"])
        if task_id not in plan[key]:
            plan[key].append(task_id)
    return dict(plan)


def _number(value: str) -> str:
    """将公开聚合中的数字格式化为便于审阅的稳定文本。"""
    if value == "unavailable":
        return value
    try:
        number = float(value)
    except ValueError:
        return value
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _memory_rounds(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    """返回可由公开 G4 明细确认的命中和复用 task ID。"""
    hits: list[str] = []
    reuse: list[str] = []
    for row in rows:
        task_id = row["task_id"]
        if float(row["memory_hit_count"]) > 0:
            hits.append(task_id)
        if float(row["memory_reuse_count"]) > 0:
            reuse.append(task_id)
    return hits, reuse


def build_report(spec: dict[str, Any], dataset_rows: list[dict[str, str]], memory_rows: list[dict[str, str]]) -> str:
    """生成 P3 中文报告，所有结论均限定在公开字段可支持的范围内。"""
    plan = unique_task_plan(spec)
    memory_by_group: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in memory_rows:
        memory_by_group[(row["dataset"], row["group_id"])].append(row)

    lines = [
        "# M9 数据集与关联连续任务分析",
        "",
        "## 数据边界",
        "",
        "本报告只读取正式 `experiments/m9_experiment_spec.json` 的任务计划，以及 `reports/m9/` 中已经生成的公开聚合 CSV。报告不读取 private attempts、candidate code、raw responses、hidden tests 或模型服务。",
        "",
        f"- `task_plan_count`：{spec['task_plan_count']}",
        f"- `task_plan_sha256`：`{spec['task_plan_sha256']}`",
        "- 任务顺序：以 manifest 的 `plan_index` 为准；下表中的任务 ID 未重新命名。",
        "",
        "## 数据集与实验组指标",
        "",
        "| 数据集 | 实验组 | 记录数 | 任务成功率 | official-test 通过率 | 平均总 Token | 平均延迟（秒） | StateVector 次数 | StateVector 字节 | 模型质量失败 | 基础设施失败 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(dataset_rows, key=lambda item: (item["dataset"], item["experiment_group"])):
        lines.append(
            "| {dataset} | {experiment_group} | {record_count} | {task_success} | {official_test_pass_rate} | {total_tokens} | {latency} | {state_count} | {state_bytes} | {quality_failure} | {infra_failure} |".format(
                dataset=row["dataset"],
                experiment_group=row["experiment_group"],
                record_count=row["record_count"],
                task_success=_number(row["task_success"]),
                official_test_pass_rate=_number(row["official_test_pass_rate"]),
                total_tokens=_number(row["total_tokens"]),
                latency=_number(row["provider_latency_seconds"]),
                state_count=_number(row["state_vector_count"]),
                state_bytes=_number(row["state_vector_bytes"]),
                quality_failure=row["model_quality_failure"],
                infra_failure=row["infrastructure_failure"],
            )
        )

    lines.extend(["", "## 关联连续任务", ""])
    for (dataset, group_id), task_ids in sorted(plan.items()):
        lines.extend(
            [
                f"### {dataset} / {group_id}",
                "",
                f"固定顺序（{len(task_ids)} 个任务）：`" + "`、`".join(task_ids) + "`。",
                "",
                "该组在每个 seed 下按 manifest 顺序连续执行；两组各 5 个任务，因此每个 dataset 的关联任务设计包含 10 个连续轮次。正式实验中的 G1-G4 和 3 个 seed 是重复的实验条件，不改变组内任务顺序。",
                "",
                "可理论复用的经验：" + ("列表重排任务之间可能共享边界条件和索引处理经验。" if "list_rearrangement" in group_id or "list_transforms" in group_id else "字符串匹配或字符串变换任务之间可能共享输入规范化和边界处理经验。"),
                "",
                "SharedMemory reset 边界：由正式 Spec 固定为 `dataset`、`experiment_group`、`seed`；不同 dataset、实验组或 seed 之间不共享实例。",
            ]
        )
        memory_rows_for_group = memory_by_group.get((dataset, group_id), [])
        if memory_rows_for_group:
            hits, reuse = _memory_rounds(memory_rows_for_group)
            lines.extend(
                [
                    "",
                    "G4 公开 Memory 明细：",
                    f"- 可确认发生 hit 的 task ID：`" + "`、`".join(hits) + "`。",
                    f"- 可确认发生 reuse 的 task ID：`" + "`、`".join(reuse) + "`。",
                    "- accept、reject、abstain、注入 Token 和 effective reuse 未在公开字段中记录，保持 `unavailable`。",
                    "- 是否存在因 Memory 导致的因果负迁移不能由该明细单独判定；只能结合 G3/G4 的固定任务结果描述为观察到的质量差异。",
                ]
            )
        else:
            lines.extend(["", "该组没有 G4 Memory 明细；Memory hit、reuse 和 reset 内部轮次不从其他指标推测。"])

    lines.extend(
        [
            "",
            "## 失败分布与解释边界",
            "",
            "公开聚合显示，失败记录按 `model_quality_failure` 和 `infrastructure_failure` 分开统计。P3 不把 official-test 失败改写为基础设施失败，也不使用 private test 内容解释具体失败原因。",
            "",
            "对于 MBPP 和 HumanEval+，表格给出 dataset×G1-G4 的任务成功率、official-test 通过率、总 Token、延迟、StateVector 和失败计数。通信 Token 分层、StateVector 等价文本、Memory 门控及有效复用仍按 P2 规则保持 `unavailable`。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    """从公开聚合生成关联连续任务说明文档。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--dataset-summary", type=Path, required=True)
    parser.add_argument("--memory-detail", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = build_report(spec, read_csv(args.dataset_summary), read_csv(args.memory_detail))
    args.output.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
