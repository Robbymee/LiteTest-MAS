import json
from pathlib import Path

from scripts.build_m9_spec import build_spec


def nested_keys(value):
    if isinstance(value, dict):
        yield from value
        for child in value.values():
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def test_formal_spec_is_fixed_public_and_complete():
    spec = json.loads((Path(__file__).resolve().parents[1] / "experiments/m9_experiment_spec.json").read_text(encoding="utf8"))
    assert spec == build_spec(spec["implementation_git_sha"])
    assert spec["task_plan_count"] == 240
    identities = {(item["seed"], item["experiment_group"], item["dataset"], item["task_id"]) for item in spec["task_plan"]}
    assert len(identities) == 240
    assert [item["plan_index"] for item in spec["task_plan"]] == list(range(240))
    assert spec["generation_parameters"] == {
        "temperature": 0, "max_tokens": 256, "timeout_seconds": 300,
        "max_retries": 1, "retry": 1, "concurrency": 1, "stream": False,
    }
    assert not {"hidden_reference_tests", "canonical_solution", "reference_solution", "official_tests"} & set(nested_keys(spec))
