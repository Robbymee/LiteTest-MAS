"""M9.1 批量 Runner 入口，默认 dry-run，正式执行需显式 freeze SHA。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_1_runner import run_batch


def main() -> int:
    """执行 M9.1 dry-run 或带 checkpoint 的正式批量循环。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--backend", choices=("mock", "openai_compatible"), default="mock")
    parser.add_argument("--freeze-git-sha")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if not args.dry_run:
        if not args.freeze_git_sha:
            raise SystemExit("formal M9.1 execution requires --freeze-git-sha")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if head != args.freeze_git_sha:
            raise SystemExit("formal M9.1 execution must run at the declared freeze SHA")
    result = run_batch(ROOT, spec, args.output_root, args.backend, args.freeze_git_sha, dry_run=args.dry_run, resume=args.resume)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
