"""Create a deterministic, review-only MBPP candidate manifest from unified tasks."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a review-only MBPP candidate list.")
    parser.add_argument("--input", default="datasets/processed/mbpp/mbpp_tasks.jsonl")
    parser.add_argument("--output", default="datasets/manifests/mbpp_candidate_list.json")
    args = parser.parse_args()
    path = Path(args.input)
    if not path.is_file():
        print(f"Candidate generation failed: input does not exist: {path}")
        return 2
    tasks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidates = []
    for task in tasks:
        visible = task["agent_visible_context"]
        candidates.append({
            "task_id": task["task_id"], "source_task_id": task["source_task_id"],
            "function_name": visible["function_name"], "signature": visible["signature"],
            "risk_tags": task["risk_tags"], "description_preview": visible["task_description"].splitlines()[0][:160],
            "status": "candidate_pending_human_review",
        })
    buckets = defaultdict(list)
    for candidate in candidates:
        key = candidate["risk_tags"][0] if candidate["risk_tags"] else "general"
        buckets[key].append(candidate["task_id"])
    recommended_groups = []
    for label, ids in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0])):
        if len(ids) >= 5 and len(recommended_groups) < 2:
            recommended_groups.append({"label": label, "task_ids": sorted(ids)[:5], "status": "recommendation_pending_human_review"})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source_dataset": "mbpp_sanitized", "candidate_count": len(candidates), "candidates": candidates, "recommended_groups": recommended_groups, "selection_notice": "This manifest is not a final experiment selection. Human review is required."}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "recommended_group_count": len(recommended_groups), "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
