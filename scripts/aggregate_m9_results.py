from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_m9_run import FORBIDDEN, verify


COMPARISONS = (("G2", "G1"), ("G3", "G2"), ("G4", "G3"), ("G4", "G1"))
METRICS = (
    "task_success",
    "official_test_pass_rate",
    "total_tokens",
    "latency_seconds",
    "state_vector_count",
    "state_vector_bytes",
    "memory_read_count",
    "memory_hit_count",
    "memory_reuse_count",
    "memory_write_count",
)
TASK_FIELDS = (
    "seed", "experiment_group", "dataset", "group_id", "task_id", "plan_index", "final_status",
    "task_success", "official_test_count", "official_test_pass_count", "official_test_fail_count",
    "official_test_pass_rate", "prompt_tokens", "completion_tokens", "total_tokens", "latency_seconds",
    "message_count", "text_character_count", "protocol_event_count", "state_vector_count", "state_vector_bytes",
    "memory_read_count", "memory_hit_count", "memory_reuse_count", "memory_write_count",
    "infrastructure_failure", "model_quality_failure", "parse_status", "usage_available",
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(recursive_keys(child) for child in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(recursive_keys(child) for child in value)) if value else set()
    return set()


def read_public_tasks(run_root: Path) -> list[dict[str, Any]]:
    tasks_dir = run_root / "public" / "tasks"
    records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tasks_dir.glob("*.json"))]
    forbidden = FORBIDDEN & set().union(*(recursive_keys(record) for record in records)) if records else set()
    if forbidden:
        raise ValueError("forbidden_public_fields:" + ",".join(sorted(forbidden)))
    return records


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("empty_values")
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def bootstrap_mean_ci(deltas: list[float], *, resamples: int, confidence: float, seed: int) -> dict[str, float | int]:
    if not deltas:
        raise ValueError("empty_paired_values")
    generator = random.Random(seed)
    count = len(deltas)
    samples = sorted(sum(deltas[generator.randrange(count)] for _ in range(count)) / count for _ in range(resamples))
    alpha = (1 - confidence) / 2
    return {
        "paired_count": count,
        "mean_difference": mean(deltas),
        "ci_lower": percentile(samples, alpha),
        "ci_upper": percentile(samples, 1 - alpha),
    }


def metric_value(record: dict[str, Any], metric: str) -> float:
    value = record[metric]
    if metric == "task_success":
        return float(bool(value))
    if value is None:
        raise ValueError(f"unavailable_metric:{metric}")
    return float(value)


def summarize(records: Iterable[dict[str, Any]], dimensions: dict[str, Any]) -> dict[str, Any]:
    rows = list(records)
    if not rows:
        raise ValueError("empty_summary")
    official_count = sum(row["official_test_count"] for row in rows)
    official_pass = sum(row["official_test_pass_count"] for row in rows)
    result = {
        **dimensions,
        "task_count": len(rows),
        "task_success_count": sum(bool(row["task_success"]) for row in rows),
        "task_success_rate": sum(bool(row["task_success"]) for row in rows) / len(rows),
        "official_test_count": official_count,
        "official_test_pass_count": official_pass,
        "official_test_fail_count": sum(row["official_test_fail_count"] for row in rows),
        "official_test_pass_rate": official_pass / official_count if official_count else None,
        "parse_success_count": sum(row["parse_status"] == "success" for row in rows),
        "infrastructure_failure_count": sum(bool(row["infrastructure_failure"]) for row in rows),
        "model_quality_failure_count": sum(bool(row["model_quality_failure"]) for row in rows),
    }
    for metric in METRICS[2:]:
        values = [metric_value(row, metric) for row in rows]
        result[f"mean_{metric}"] = mean(values)
        result[f"sum_{metric}"] = sum(values)
    return result


def paired_comparisons(records: list[dict[str, Any]], bootstrap: dict[str, Any]) -> list[dict[str, Any]]:
    by_group = defaultdict(dict)
    for record in records:
        identity = (record["seed"], record["dataset"], record["task_id"])
        by_group[record["experiment_group"]][identity] = record
    results = []
    for treatment, control in COMPARISONS:
        treatment_rows = by_group[treatment]
        control_rows = by_group[control]
        identities = sorted(set(treatment_rows) & set(control_rows))
        if len(identities) != len(treatment_rows) or len(identities) != len(control_rows):
            raise ValueError(f"unpaired_records:{treatment}_vs_{control}")
        for metric_index, metric in enumerate(METRICS):
            deltas = [metric_value(treatment_rows[identity], metric) - metric_value(control_rows[identity], metric) for identity in identities]
            seed_material = f"{bootstrap['seed']}:{treatment}:{control}:{metric}:{metric_index}".encode("utf-8")
            seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
            result = bootstrap_mean_ci(deltas, resamples=bootstrap["resamples"], confidence=bootstrap["confidence"], seed=seed)
            results.append({
                "treatment_group": treatment,
                "control_group": control,
                "metric": metric,
                "difference_direction": "treatment_minus_control",
                "bootstrap_resamples": bootstrap["resamples"],
                "confidence": bootstrap["confidence"],
                **result,
            })
    return results


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({field for row in rows for field, value in row.items() if not isinstance(value, (dict, list))})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field) for field in fields} for row in rows])


def aggregate(run_root: Path, spec_path: Path, output_dir: Path, expected_freeze_sha: str, plan_root: Path = ROOT) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    strict = verify(run_root, spec, root=plan_root, strict=True, expected_freeze_sha=expected_freeze_sha)
    if not strict["valid"]:
        raise ValueError("strict_verifier_failed:" + ",".join(strict["errors"]))
    records = read_public_tasks(run_root)
    if len(records) != spec["task_plan_count"]:
        raise ValueError("unexpected_final_count")
    task_rows = [{field: record[field] for field in TASK_FIELDS} for record in records]
    group_rows = [summarize(rows, {"experiment_group": group}) for group, rows in sorted(_partition(records, "experiment_group").items())]
    dataset_rows = [summarize(rows, {"dataset": dataset}) for dataset, rows in sorted(_partition(records, "dataset").items())]
    seed_rows = [summarize(rows, {"seed": seed}) for seed, rows in sorted(_partition(records, "seed").items())]
    comparison_rows = paired_comparisons(records, spec["bootstrap"])
    manifest = {
        "schema_version": "1.0",
        "result_scope": spec["result_scope"],
        "freeze_git_sha": expected_freeze_sha,
        "spec_sha256": records[0]["spec_sha256"],
        "implementation_git_sha": spec["implementation_git_sha"],
        "model": spec["model"],
        "task_plan_sha256": spec["task_plan_sha256"],
        "final_record_count": len(records),
        "public_task_file_count": len(list((run_root / "public" / "tasks").glob("*.json"))),
        "strict_verifier": {"valid": strict["valid"], "inventory_sha256": strict["inventory"]["inventory_sha256"]},
        "bootstrap": spec["bootstrap"],
        "public_leakage_scan": {"forbidden_fields": [], "leakage_count": 0},
        "aggregate_input_sha256": hashlib.sha256(canonical(task_rows).encode("utf-8")).hexdigest(),
    }
    deterministic = {"manifest": manifest, "groups": group_rows, "datasets": dataset_rows, "seeds": seed_rows, "comparisons": comparison_rows}
    manifest["deterministic_aggregate_sha256"] = hashlib.sha256(canonical(deterministic).encode("utf-8")).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "m9_aggregate_manifest.json": manifest,
        "m9_aggregate_tasks.json": task_rows,
        "m9_aggregate_groups.json": group_rows,
        "m9_aggregate_datasets.json": dataset_rows,
        "m9_aggregate_seeds.json": seed_rows,
        "m9_paired_comparisons.json": comparison_rows,
    }
    for name, value in artifacts.items():
        write_json(output_dir / name, value)
    for name, rows in (("m9_tasks.csv", task_rows), ("m9_groups.csv", group_rows), ("m9_datasets.csv", dataset_rows), ("m9_seeds.csv", seed_rows), ("m9_paired_comparisons.csv", comparison_rows)):
        write_csv(output_dir / name, rows)
    report = ["# M9 Formal Aggregate", "", f"result_scope: `{spec['result_scope']}`", f"", f"final records: `{len(records)}`", f"strict verifier: `passed`", f"bootstrap: `{spec['bootstrap']['resamples']}` resamples, `{spec['bootstrap']['confidence']}` confidence", "", "All comparisons are paired by `(seed, dataset, task_id)` and report treatment minus control. These summaries use public formal records only.", ""]
    (output_dir / "m9_aggregate_report.md").write_text("\n".join(report), encoding="utf-8")
    return manifest


def _partition(records: list[dict[str, Any]], field: str) -> dict[Any, list[dict[str, Any]]]:
    buckets: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[record[field]].append(record)
    return buckets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-freeze-sha", required=True)
    parser.add_argument("--plan-root", help="read-only checkout containing the frozen local task plan")
    args = parser.parse_args()
    try:
        result = aggregate(
            Path(args.run_root), Path(args.spec), Path(args.output_dir), args.expected_freeze_sha,
            Path(args.plan_root) if args.plan_root else ROOT,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"m9 aggregation failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
