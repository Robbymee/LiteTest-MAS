from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.orchestrator import Orchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one LiteTest-MAS benchmark task.")
    parser.add_argument("--mode", choices=["text", "protocol"], required=True)
    parser.add_argument("--task", required=True, help="Path to a LiteTest benchmark JSON task.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = PROJECT_ROOT / task_path

    result = Orchestrator(PROJECT_ROOT).run(mode=args.mode, task_path=task_path)
    print(json.dumps(result, indent=2))
    return 0 if result["metrics"]["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
