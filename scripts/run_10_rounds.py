from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.orchestrator import Orchestrator


DATASET_DIR = PROJECT_ROOT / "datasets" / "litetest_bench"
DEFAULT_MODES = ("text", "protocol")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LiteTest-MAS across benchmark tasks.")
    parser.add_argument(
        "--tasks",
        default="",
        help="Comma-separated task ids such as A01,A02,B01. Default: all tasks in datasets/litetest_bench.",
    )
    parser.add_argument(
        "--group",
        choices=["A", "B"],
        help="Optional group filter. Applied after task discovery.",
    )
    parser.add_argument(
        "--modes",
        default="text,protocol",
        help="Comma-separated modes. Default: text,protocol",
    )
    return parser.parse_args()


def parse_modes(raw: str) -> list[str]:
    modes = [item.strip() for item in raw.split(",") if item.strip()]
    if not modes:
        raise ValueError("At least one mode must be provided.")
    invalid = [mode for mode in modes if mode not in DEFAULT_MODES]
    if invalid:
        raise ValueError(f"Unsupported modes: {', '.join(invalid)}")
    return modes


def discover_task_paths(task_ids_raw: str, group_id: str | None) -> list[Path]:
    if task_ids_raw.strip():
        task_ids = [item.strip() for item in task_ids_raw.split(",") if item.strip()]
        task_paths = [DATASET_DIR / f"{task_id}.json" for task_id in task_ids]
    else:
        task_paths = sorted(DATASET_DIR.glob("*.json"))

    resolved_paths = []
    for task_path in task_paths:
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")
        if group_id is None:
            resolved_paths.append(task_path)
            continue
        task = json.loads(task_path.read_text(encoding="utf-8"))
        if task["group_id"] == group_id:
            resolved_paths.append(task_path)
    return resolved_paths


def build_summary(results: list[dict]) -> dict:
    by_mode: dict[str, dict] = {}
    for result in results:
        metrics = result["metrics"]
        mode = metrics["mode"]
        bucket = by_mode.setdefault(
            mode,
            {
                "run_count": 0,
                "success_count": 0,
                "agent_message_count_total": 0,
                "char_count_total": 0,
                "token_count_total": 0,
                "total_duration_sec": 0.0,
            },
        )
        bucket["run_count"] += 1
        bucket["success_count"] += 1 if metrics["success"] else 0
        bucket["agent_message_count_total"] += metrics["agent_message_count"]
        bucket["char_count_total"] += metrics["char_count_total"]
        bucket["token_count_total"] += metrics["token_count_total"]
        bucket["total_duration_sec"] += metrics["total_duration_sec"]

    aggregates = {}
    for mode, bucket in by_mode.items():
        run_count = bucket["run_count"]
        aggregates[mode] = {
            "run_count": run_count,
            "success_count": bucket["success_count"],
            "success_rate": bucket["success_count"] / run_count if run_count else 0.0,
            "avg_agent_message_count": bucket["agent_message_count_total"] / run_count if run_count else 0.0,
            "avg_char_count_total": bucket["char_count_total"] / run_count if run_count else 0.0,
            "avg_token_count_total": bucket["token_count_total"] / run_count if run_count else 0.0,
            "avg_total_duration_sec": bucket["total_duration_sec"] / run_count if run_count else 0.0,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_count": len({item["task_id"] for item in results}),
        "run_count": len(results),
        "aggregates_by_mode": aggregates,
        "results": results,
    }


def write_summary(summary: dict) -> Path:
    summary_dir = PROJECT_ROOT / "runs"
    summary_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = summary_dir / f"summary_10_rounds_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def main() -> int:
    args = parse_args()
    modes = parse_modes(args.modes)
    task_paths = discover_task_paths(args.tasks, args.group)
    orchestrator = Orchestrator(PROJECT_ROOT)

    results = []
    overall_success = True
    for task_path in task_paths:
        task = json.loads(task_path.read_text(encoding="utf-8"))
        for mode in modes:
            outcome = orchestrator.run(mode=mode, task_path=task_path)
            results.append(
                {
                    "task_id": task["task_id"],
                    "group_id": task["group_id"],
                    "mode": mode,
                    "run_dir": outcome["run_dir"],
                    "metrics": outcome["metrics"],
                }
            )
            overall_success = overall_success and outcome["metrics"]["success"]

    summary = build_summary(results)
    summary_path = write_summary(summary)
    print(json.dumps({"summary_path": str(summary_path), "summary": summary}, indent=2))
    return 0 if overall_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
