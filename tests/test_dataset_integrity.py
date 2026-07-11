import json
from pathlib import Path
import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "datasets" / "litetest_bench"
EXPECTED_TASKS = [
    "A01",
    "A02",
    "A03",
    "A04",
    "A05",
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
]
REQUIRED_KEYS = {
    "task_id",
    "group_id",
    "topic",
    "function_name",
    "task_description",
    "signature",
    "code_under_test",
    "risk_tags",
    "expected_test_focus",
    "hidden_reference_tests",
    "cases",
}


def load_task(task_id: str) -> dict:
    task_path = DATASET_DIR / f"{task_id}.json"
    return json.loads(task_path.read_text(encoding="utf-8"))


def test_all_expected_tasks_exist():
    actual = sorted(path.stem for path in DATASET_DIR.glob("*.json"))
    assert actual == EXPECTED_TASKS


def test_all_tasks_have_required_fields():
    for task_id in EXPECTED_TASKS:
        task = load_task(task_id)
        assert REQUIRED_KEYS.issubset(task.keys())
        assert task["task_id"] == task_id
        assert task["group_id"] in {"A", "B"}
        assert task["function_name"]
        assert isinstance(task["risk_tags"], list) and task["risk_tags"]
        assert isinstance(task["expected_test_focus"], list) and task["expected_test_focus"]
        assert isinstance(task["hidden_reference_tests"], list) and task["hidden_reference_tests"]
        assert isinstance(task["cases"], list) and task["cases"]


def test_all_code_under_test_can_exec_and_define_target_function():
    for task_id in EXPECTED_TASKS:
        task = load_task(task_id)
        namespace: dict[str, object] = {}
        exec(task["code_under_test"], namespace)
        function_obj = namespace.get(task["function_name"])
        assert isinstance(function_obj, types.FunctionType)


def test_all_cases_have_inputs_and_expected_values():
    for task_id in EXPECTED_TASKS:
        task = load_task(task_id)
        for case in task["cases"]:
            assert isinstance(case["input"], dict)
            assert "expected" in case


def test_group_specific_risk_tags_are_present():
    for task_id in EXPECTED_TASKS:
        task = load_task(task_id)
        tags = set(task["risk_tags"])
        if task["group_id"] == "A":
            assert "string" in tags
            assert "empty_input" in tags
            assert "invalid_format" in tags
        if task["group_id"] == "B":
            assert "empty_input" in tags
            assert "nested_structure" in tags or "missing_key" in tags or "duplicate" in tags
