import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_humaneval_candidates.py"
PROCESSED = ROOT / "datasets" / "processed" / "humaneval_plus" / "humaneval_plus_tasks.jsonl"
BLOCKED = {"canonical_solution", "code_under_test", "hidden_reference_tests", "test", "contract", "base_input", "plus_input"}


def nested_keys(value):
    if isinstance(value, dict):
        yield from value
        for child in value.values(): yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value: yield from nested_keys(child)


def test_humaneval_manifests_are_safe_stable_and_resolve_to_processed_data(tmp_path):
    candidate, review, selected = (tmp_path / name for name in ("candidates.json", "review.json", "selected.json"))
    completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(PROCESSED), "--candidate-output", str(candidate), "--review-output", str(review), "--selected-output", str(selected)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr
    candidate_data, review_data, selected_data = (json.loads(path.read_text(encoding="utf-8")) for path in (candidate, review, selected))
    assert candidate_data["candidate_count"] == 164
    assert review_data["scheme_count"] == 3
    assert selected_data["selection_status"] == "delegated_review_approved"
    assert selected_data["reviewer_type"] == "codex_technical_review_under_user_authorization"
    assert len(selected_data["groups"]) == 2
    ids = [task_id for group in selected_data["groups"] for task_id in group["task_ids"]]
    assert len(ids) == len(set(ids)) == 10
    processed = {item["task_id"]: item for item in map(json.loads, PROCESSED.read_text(encoding="utf-8").splitlines())}
    for group in selected_data["groups"]:
        assert group["sequence_order"] == [1, 2, 3, 4, 5]
        assert [processed[task_id]["function_name"] for task_id in group["task_ids"]] == group["expected_function_names"]
    for path, payload in ((candidate, candidate_data), (review, review_data), (selected, selected_data)):
        assert not (set(nested_keys(payload)) & BLOCKED)
        assert json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n" == path.read_text(encoding="utf-8")
