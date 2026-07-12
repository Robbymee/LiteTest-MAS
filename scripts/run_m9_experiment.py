from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.m9_runner import resume_or_execute, select_plan, spec_sha256, validate_spec, verify_inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--combination")
    parser.add_argument("--task-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-one", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--freeze-git-sha")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf8"))
    validate_spec(spec, spec["implementation_git_sha"])
    items = verify_inventory(ROOT, spec)
    selected = select_plan(items, args.combination) if args.combination else items
    if args.task_id:
        selected = [item for item in selected if item["task_id"] == args.task_id]
    if (args.combination or args.task_id) and len(selected) != 1:
        raise SystemExit("combination/task selection must resolve exactly one task")
    if args.execute_one:
        if len(selected) != 1:
            raise SystemExit("--execute-one requires --combination and --task-id")
        if args.strict and not args.freeze_git_sha:
            raise SystemExit("--strict --execute-one requires --freeze-git-sha")
        from llm.config import LLMConfig, create_backend
        record, resumed_skip = resume_or_execute(ROOT, selected[0], args.output_root, create_backend(LLMConfig.from_env()), spec, args.freeze_git_sha, items, resume=args.resume)
        print(json.dumps({"final_status": record["final_status"], "task_id": record["task_id"], "resumed_skip": resumed_skip}, sort_keys=True))
        return
    print(json.dumps({"planned": len(items), "selected": len(selected), "duplicates": len(items) - len({tuple(sorted(item.items())) for item in items}), "spec_sha256": spec_sha256(spec), "dry_run": args.dry_run}, sort_keys=True))


if __name__ == "__main__":
    main()
