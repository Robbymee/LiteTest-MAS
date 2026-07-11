from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.sequence_runner import SelectedTaskLoader, SequenceRunner, SequenceValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic M2.2 MBPP task sequences.")
    parser.add_argument("--selection", default="datasets/manifests/mbpp_selected_groups.json")
    parser.add_argument("--tasks", default="datasets/processed/mbpp/mbpp_tasks.jsonl")
    parser.add_argument("--mode", choices=["text", "protocol", "both"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="runs/m2_2")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    try:
        manifest, tasks = SelectedTaskLoader(PROJECT_ROOT / args.selection, PROJECT_ROOT / args.tasks).load()
        modes = ["text", "protocol"] if args.mode == "both" else [args.mode]
        results = []
        for mode in modes:
            runner = SequenceRunner(manifest, tasks, mode, args.seed)
            output = PROJECT_ROOT / args.output_dir
            if args.mode == "both":
                output = output / f"{mode}_seed{args.seed}"
            result = runner.run(output, dry_run=args.dry_run, continue_on_error=args.continue_on_error)
            results.append({"mode": mode, "plan": result["plan"], "summary": result["summary"]})
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if all(item["summary"] is None or item["summary"]["completion_status"] == "complete" for item in results) else 1
    except (OSError, SequenceValidationError, json.JSONDecodeError) as error:
        print(f"M2.2 sequence run failed: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
