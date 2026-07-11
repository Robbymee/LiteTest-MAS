"""Import a locally downloaded HumanEval+ JSONL/JSONL.GZ file without execution."""

from __future__ import annotations

import argparse
import ast
import gzip
import json
from pathlib import Path


SOURCE_DATASET = "humaneval_plus"
IMPORT_VERSION = "m2.3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a local HumanEval+ JSONL file.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="datasets/processed/humaneval_plus")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def _read_records(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"HumanEval+ input file does not exist: {path}")
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _convert(record: dict) -> dict:
    required = ("task_id", "prompt", "entry_point", "canonical_solution", "test")
    missing = [name for name in required if not record.get(name)]
    if missing:
        raise ValueError(f"Missing required HumanEval+ fields: {', '.join(missing)}")
    code = record["prompt"] + record["canonical_solution"]
    try:
        tree = ast.parse(code)
        compile(code, "<humaneval_plus_code_under_test>", "exec")
    except SyntaxError as error:
        raise ValueError(f"code_under_test does not compile: {error.msg}") from error
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == record["entry_point"]), None)
    if function is None:
        raise ValueError("entry_point is not a top-level function in code_under_test")
    signature = f"{function.name}({ast.unparse(function.args)})"
    task_description = record["prompt"]
    visible = {
        "task_description": task_description,
        "function_name": function.name,
        "signature": signature,
        "entry_point": function.name,
        "code_under_test": code,
    }
    hidden = [{key: record.get(key) for key in ("test", "contract", "base_input", "plus_input", "atol")}]
    return {
        "task_id": f"{SOURCE_DATASET}:{record['task_id']}",
        "source_dataset": SOURCE_DATASET,
        "source_task_id": record["task_id"],
        "task_description": task_description,
        "function_name": function.name,
        "signature": signature,
        "entry_point": function.name,
        "code_under_test": code,
        "risk_tags": [],
        "hidden_reference_tests": hidden,
        "agent_visible_context": visible,
        "provenance": {"dataset_name": "HumanEval+", "original_task_id": record["task_id"], "import_version": IMPORT_VERSION},
    }


def main() -> int:
    args = parse_args()
    try:
        records = _read_records(Path(args.input))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"HumanEval+ import failed: {error}")
        return 2
    tasks, errors = [], []
    for index, record in enumerate(records):
        try:
            tasks.append(_convert(record))
        except (TypeError, ValueError) as error:
            errors.append({"record_index": index, "error": str(error)})
    tasks.sort(key=lambda task: task["source_task_id"])
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "humaneval_plus_tasks.jsonl").write_text("".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in tasks), encoding="utf-8")
    (output / "import_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "metadata.json").write_text(json.dumps({"dataset_name": "HumanEval+", "source_record_count": len(records), "imported_task_count": len(tasks), "error_count": len(errors), "import_version": IMPORT_VERSION}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"imported_task_count": len(tasks), "error_count": len(errors), "output_dir": str(output)}))
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
