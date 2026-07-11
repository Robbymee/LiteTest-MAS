"""Import locally supplied MBPP-Sanitized data without executing dataset code."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IMPORT_VERSION = "m2.0"
SOURCE_DATASET = "mbpp_sanitized"
DEFAULT_OUTPUT_DIR = Path("datasets") / "processed" / "mbpp"


@dataclass(frozen=True)
class ImportResult:
    tasks: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    input_count: int


class RecordValidationError(ValueError):
    """A single source record cannot be converted into a unified task."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a local MBPP-Sanitized JSON or JSONL file.")
    parser.add_argument("--input", required=True, help="Local JSON or JSONL input file; no download is attempted.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for mbpp_tasks.jsonl and import reports.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of valid, sorted tasks to write.")
    parser.add_argument("--strict", action="store_true", help="Fail if any source record is invalid.")
    return parser.parse_args()


def _read_json_records(input_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {input_path}: {error.msg} (line {error.lineno}).") from error

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("tasks", payload.get("data"))
        if records is None:
            raise ValueError("JSON object must contain a list under 'tasks' or 'data'.")
    else:
        raise ValueError("JSON input must be a list or an object containing 'tasks' or 'data'.")

    if not isinstance(records, list):
        raise ValueError("The JSON task collection must be a list.")
    return records


def _read_jsonl_records(input_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append({"record_index": line_number - 1, "error": f"Invalid JSONL: {error.msg}"})
            continue
        records.append(value)
    return records, errors


def read_records(input_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not input_path.exists():
        raise FileNotFoundError(f"MBPP input file does not exist: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"MBPP input path is not a file: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".json":
        return _read_json_records(input_path), []
    if suffix == ".jsonl":
        return _read_jsonl_records(input_path)
    raise ValueError(f"Unsupported input format '{input_path.suffix}'. Use a .json or .jsonl file.")


def _required_string(record: dict[str, Any], names: tuple[str, ...], label: str) -> str:
    for name in names:
        value = record.get(name)
        if isinstance(value, str) and value.strip():
            return value
    raise RecordValidationError(f"Missing non-empty {label}; expected one of: {', '.join(names)}.")


def _source_task_id(record: dict[str, Any]) -> str:
    for name in ("task_id", "source_task_id"):
        value = record.get(name)
        if value is not None and str(value).strip():
            return str(value)
    raise RecordValidationError("Missing source task ID; expected 'task_id' or 'source_task_id'.")


def _hidden_tests(record: dict[str, Any]) -> list[Any]:
    for name in ("test_list", "hidden_reference_tests"):
        if name in record:
            value = record[name]
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return [value]
            raise RecordValidationError(f"Field '{name}' must be a list or string.")
    raise RecordValidationError("Missing hidden reference tests; expected 'test_list' or 'hidden_reference_tests'.")


def _entry_function(code_under_test: str) -> tuple[str, str]:
    try:
        tree = ast.parse(code_under_test)
        compile(code_under_test, "<mbpp_code_under_test>", "exec")
    except (SyntaxError, ValueError) as error:
        raise RecordValidationError(f"code_under_test does not compile: {error.msg if isinstance(error, SyntaxError) else error}") from error

    function = next((node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
    if function is None:
        raise RecordValidationError("code_under_test must define a top-level function.")
    return function.name, f"{function.name}({ast.unparse(function.args)})"


def build_risk_tags(task_description: str, signature: str, code_under_test: str) -> list[str]:
    """Create deterministic tags from agent-visible static fields only."""
    text = " ".join((task_description, signature, code_under_test)).lower()
    checks = {
        "empty_input": ("empty", "len(", "not "),
        "string": ("string", "str", "split", "join"),
        "list": ("list", "[", "append"),
        "dictionary": ("dict", "dictionary", ".get("),
        "numeric": ("integer", "number", "float", "%", "+", "-"),
    }
    return sorted(tag for tag, markers in checks.items() if any(marker in text for marker in markers))


def convert_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise RecordValidationError("Source record must be a JSON object.")

    source_task_id = _source_task_id(record)
    task_description = _required_string(record, ("text", "task_description"), "task description")
    code_under_test = _required_string(record, ("code", "code_under_test"), "reference implementation")
    hidden_reference_tests = _hidden_tests(record)
    function_name, signature = _entry_function(code_under_test)
    agent_visible_context = {
        "task_description": task_description,
        "function_name": function_name,
        "signature": signature,
        "entry_point": function_name,
        "code_under_test": code_under_test,
    }
    return {
        "task_id": f"{SOURCE_DATASET}:{source_task_id}",
        "source_dataset": SOURCE_DATASET,
        "source_task_id": source_task_id,
        "task_description": task_description,
        "function_name": function_name,
        "signature": signature,
        "entry_point": function_name,
        "code_under_test": code_under_test,
        "risk_tags": build_risk_tags(task_description, signature, code_under_test),
        "hidden_reference_tests": hidden_reference_tests,
        "agent_visible_context": agent_visible_context,
        "provenance": {
            "dataset_name": "MBPP-Sanitized",
            "original_task_id": source_task_id,
            "import_version": IMPORT_VERSION,
        },
    }


def import_mbpp(input_path: Path, limit: int | None = None) -> ImportResult:
    if limit is not None and limit < 0:
        raise ValueError("--limit must be zero or greater.")
    records, read_errors = read_records(input_path)
    errors = list(read_errors)
    tasks: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        try:
            tasks.append(convert_record(record))
        except RecordValidationError as error:
            errors.append({"record_index": index, "error": str(error)})
    tasks.sort(key=lambda task: (task["source_task_id"], task["task_id"]))
    if limit is not None:
        tasks = tasks[:limit]
    errors.sort(key=lambda error: (error["record_index"], error["error"]))
    return ImportResult(tasks=tasks, errors=errors, input_count=len(records))


def write_outputs(result: ImportResult, output_dir: Path, input_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = output_dir / "mbpp_tasks.jsonl"
    tasks_path.write_text(
        "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in result.tasks),
        encoding="utf-8",
    )
    summary = {
        "dataset_name": "MBPP-Sanitized",
        "import_version": IMPORT_VERSION,
        "input_path": str(input_path),
        "input_record_count": result.input_count,
        "imported_task_count": len(result.tasks),
        "error_count": len(result.errors),
    }
    (output_dir / "import_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "import_errors.json").write_text(
        json.dumps(result.errors, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    try:
        result = import_mbpp(input_path=input_path, limit=args.limit)
        write_outputs(result=result, output_dir=output_dir, input_path=input_path)
    except (FileNotFoundError, ValueError) as error:
        print(f"MBPP import failed: {error}")
        return 2

    print(
        json.dumps(
            {
                "imported_task_count": len(result.tasks),
                "error_count": len(result.errors),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if args.strict and result.errors:
        print("MBPP import failed in strict mode because invalid records were found.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
