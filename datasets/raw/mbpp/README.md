# MBPP-Sanitized Raw Data

Place a manually downloaded MBPP-Sanitized JSON or JSONL file in this directory, or pass its local path directly to the importer. The importer never downloads data and does not require network access.

Raw public-dataset files are not recommended for Git commits. The repository ignores `*.json` and `*.jsonl` in this directory.

Example:

```bash
python scripts/import_mbpp.py --input datasets/raw/mbpp/mbpp_sanitized.json --output-dir datasets/processed/mbpp
```

The importer accepts the common fields `task_id`, `text` or `task_description`, `code` or `code_under_test`, and `test_list` or `hidden_reference_tests`. Formal experiments must preserve the original task ID and MBPP-Sanitized source information. Official tests are imported only as hidden reference tests and are not agent input.
