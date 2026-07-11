"""Build safe HumanEval+ candidate and delegated-review manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def tags(task: dict) -> list[str]:
    visible = task["agent_visible_context"]
    text = (visible["function_name"] + " " + visible["signature"] + " " + visible["task_description"]).lower()
    categories = {
        "string": ("str", "string", "text", "word", "char", "vowel", "prefix"),
        "list": ("list", "arr", "lst", "numbers", "sort", "filter"),
        "numeric": ("int", "float", "number", "prime", "factor", "fib"),
        "sequence_transform": ("sort", "remove", "filter", "shuffle", "concat", "reverse"),
        "predicate": ("is_", "check", "correct", "valid", "match"),
    }
    return sorted(name for name, markers in categories.items() if any(marker in text for marker in markers))


def candidate(task: dict) -> dict:
    visible = task["agent_visible_context"]
    return {
        "task_id": task["task_id"], "source_task_id": task["source_task_id"],
        "function_name": visible["function_name"], "signature": visible["signature"],
        "prompt_summary": visible["task_description"].splitlines()[0][:160],
        "algorithm_domain_tags": tags(task), "input_output_shape_tags": ["function_call"],
        "complexity_tag": "unspecified_public_metadata", "risk_tags": task.get("risk_tags", []),
        "status": "candidate_pending_delegated_review",
    }


def group(group_id: str, task_ids: list[str], rationale: str, knowledge: list[str], score: float) -> dict:
    return {"group_id": group_id, "task_ids": task_ids, "order": [1, 2, 3, 4, 5], "relation_rationale": rationale, "reusable_knowledge": knowledge, "possible_confounders": ["mock-agent validation only", "public prompt complexity differs across tasks"], "leakage_audit": "metadata and prompt summaries only; no hidden tests or solutions", "recommendation_score": score}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate safe HumanEval+ candidate review manifests.")
    parser.add_argument("--input", default="datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl")
    parser.add_argument("--candidate-output", default="datasets/manifests/humaneval_candidate_list.json")
    parser.add_argument("--review-output", default="datasets/manifests/humaneval_group_review.json")
    parser.add_argument("--selected-output", default="datasets/manifests/humaneval_selected_groups.json")
    args = parser.parse_args()
    tasks = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {task["task_id"]: task for task in tasks}
    candidates = [candidate(task) for task in sorted(tasks, key=lambda item: item["source_task_id"])]
    schemes = [
        [group("humaneval_string_transforms", ["humaneval_plus:HumanEval/27", "humaneval_plus:HumanEval/28", "humaneval_plus:HumanEval/29", "humaneval_plus:HumanEval/51", "humaneval_plus:HumanEval/86"], "String transformation progresses from case conversion and concatenation to prefix filtering, vowel removal, and character ordering.", ["empty strings", "case handling", "substring boundaries", "stable output ordering"], 0.93), group("humaneval_list_transforms", ["humaneval_plus:HumanEval/26", "humaneval_plus:HumanEval/33", "humaneval_plus:HumanEval/37", "humaneval_plus:HumanEval/70", "humaneval_plus:HumanEval/149"], "List transformation progresses through deduplication and selective sorting to ordering and filtered aggregation.", ["empty lists", "duplicates", "index parity", "ordering invariants"], 0.90)],
        [group("humaneval_numeric_properties", ["humaneval_plus:HumanEval/24", "humaneval_plus:HumanEval/25", "humaneval_plus:HumanEval/31", "humaneval_plus:HumanEval/59", "humaneval_plus:HumanEval/75"], "Number-property tasks share divisibility, factorization, primality, and boundary testing.", ["zero and one", "negative values", "divisibility", "factor boundaries"], 0.86), group("humaneval_bracket_strings", ["humaneval_plus:HumanEval/1", "humaneval_plus:HumanEval/6", "humaneval_plus:HumanEval/56", "humaneval_plus:HumanEval/61", "humaneval_plus:HumanEval/119"], "Bracket and parenthesis validation tasks support stack and balance testing reuse.", ["empty strings", "nesting", "unmatched delimiters", "sequence boundaries"], 0.82)],
        [group("humaneval_numeric_sequences", ["humaneval_plus:HumanEval/15", "humaneval_plus:HumanEval/46", "humaneval_plus:HumanEval/55", "humaneval_plus:HumanEval/63", "humaneval_plus:HumanEval/83"], "Numeric sequence construction spans simple ranges, recurrence relations, and binary-pattern sequences.", ["base cases", "recurrence", "integer boundaries", "sequence length"], 0.80), group("humaneval_string_predicates", ["humaneval_plus:HumanEval/48", "humaneval_plus:HumanEval/54", "humaneval_plus:HumanEval/64", "humaneval_plus:HumanEval/82", "humaneval_plus:HumanEval/98"], "String predicates share case, character-class, and boundary-condition testing.", ["empty strings", "case normalization", "character classes", "false cases"], 0.79)],
    ]
    for scheme in schemes:
        for item in scheme:
            for task_id in item["task_ids"]:
                if task_id not in by_id:
                    raise ValueError(f"Review task missing from processed data: {task_id}")
    selected = schemes[0]
    selected_manifest = {"schema_version": "1.0", "source_dataset": "humaneval_plus", "selection_status": "delegated_review_approved", "reviewer_type": "codex_technical_review_under_user_authorization", "selection_purpose": "related_task_sequence_experiment", "group_count": 2, "tasks_per_group": 5, "total_tasks": 10, "groups": [{**item, "expected_function_names": [by_id[task_id]["function_name"] for task_id in item["task_ids"]], "sequence_order": item["order"]} for item in selected]}
    outputs = [(args.candidate_output, {"source_dataset": "humaneval_plus", "candidate_count": len(candidates), "candidates": candidates}), (args.review_output, {"schema_version": "1.0", "scheme_count": 3, "schemes": [{"scheme_id": f"option_{index + 1}", "groups": scheme} for index, scheme in enumerate(schemes)]}), (args.selected_output, selected_manifest)]
    for name, payload in outputs:
        path = Path(name); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "selected_group_count": 2, "review_scheme_count": 3}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
