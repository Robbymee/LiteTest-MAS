import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "datasets" / "manifests" / "mbpp_selected_groups.json"
CANDIDATE_PATH = PROJECT_ROOT / "datasets" / "manifests" / "mbpp_candidate_list.json"
PROCESSED_PATH = PROJECT_ROOT / "datasets" / "processed" / "mbpp" / "mbpp_tasks.jsonl"
EXPECTED_GROUPS = {
    "mbpp_list_rearrangement": [
        "mbpp_sanitized:591",
        "mbpp_sanitized:644",
        "mbpp_sanitized:586",
        "mbpp_sanitized:743",
        "mbpp_sanitized:632",
    ],
    "mbpp_regex_string_matching": [
        "mbpp_sanitized:434",
        "mbpp_sanitized:285",
        "mbpp_sanitized:787",
        "mbpp_sanitized:794",
        "mbpp_sanitized:607",
    ],
}
BLOCKED_KEYS = {"hidden_reference_tests", "reference_solution", "canonical_solution", "tests", "test_list"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def nested_keys(value):
    if isinstance(value, dict):
        yield from value
        for child in value.values():
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def test_selection_manifest_schema_and_group_sizes():
    manifest = load_json(MANIFEST_PATH)
    assert manifest["schema_version"] == "1.0"
    assert manifest["selection_status"] == "human_approved"
    assert manifest["group_count"] == 2
    assert manifest["tasks_per_group"] == 5
    assert manifest["total_tasks"] == 10
    assert len(manifest["groups"]) == 2
    assert len({group["group_id"] for group in manifest["groups"]}) == 2
    all_ids = [task_id for group in manifest["groups"] for task_id in group["task_ids"]]
    assert len(all_ids) == 10
    assert len(set(all_ids)) == 10
    assert all(len(group["task_ids"]) == 5 for group in manifest["groups"])


def test_selection_order_functions_and_candidate_membership():
    manifest = load_json(MANIFEST_PATH)
    candidates = {item["task_id"] for item in load_json(CANDIDATE_PATH)["candidates"]}
    processed = {item["task_id"]: item for item in map(json.loads, PROCESSED_PATH.read_text(encoding="utf-8").splitlines())}
    for group in manifest["groups"]:
        assert group["task_ids"] == EXPECTED_GROUPS[group["group_id"]]
        assert group["sequence_order"] == [1, 2, 3, 4, 5]
        assert set(group["task_ids"]).issubset(candidates)
        assert set(group["task_ids"]).issubset(processed)
        assert [processed[task_id]["function_name"] for task_id in group["task_ids"]] == group["expected_function_names"]


def test_manifest_has_no_hidden_test_keys_or_test_content_and_is_stable():
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    manifest = json.loads(raw)
    assert not (set(nested_keys(manifest)) & BLOCKED_KEYS)
    processed = [json.loads(line) for line in PROCESSED_PATH.read_text(encoding="utf-8").splitlines()]
    for task in processed:
        for hidden in task["hidden_reference_tests"]:
            assert str(hidden) not in raw
    assert raw == json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
