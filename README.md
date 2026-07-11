# LiteTest-MAS

LiteTest-MAS is a minimal closed-loop experiment for validating a low-overhead multi-agent workflow for code test generation on openEuler 24.03-LTS-SP3 x86_64.

This first stage only validates Python, Git, Codex-assisted development, deterministic agent orchestration, test generation, pytest execution, and metrics collection. It does not install or run local LLMs, CUDA, Docker, iSulad, ChromaDB, FAISS, or any model runtime.

## Modes

- Text Mode: agents exchange plain natural-language text messages.
- Protocol Mode: agents exchange structured JSON-compatible messages.

## Requirements

Core code uses only the Python standard library. Pytest is only needed to execute generated tests and repository tests.

```bash
python -m pip install -r requirements.txt
```

On openEuler, use `python3` if that is the available Python command:

```bash
python3 -m pip install -r requirements.txt
```

## Acceptance Commands

Windows local:

```bash
python scripts/run_one.py --mode text --task datasets/litetest_bench/A01.json
python scripts/run_one.py --mode protocol --task datasets/litetest_bench/A01.json
```

openEuler:

```bash
python3 scripts/run_one.py --mode text --task datasets/litetest_bench/A01.json
python3 scripts/run_one.py --mode protocol --task datasets/litetest_bench/A01.json
```

Repository tests:

```bash
python -m pytest tests
```

## Outputs

Each run creates an isolated directory under `runs/<task_id>/<mode>-<timestamp>/` containing materialized source files, generated tests, pytest output, `summary.json`, and `metrics.json`.

## Dataset Shape

Each benchmark task in `datasets/litetest_bench/` uses a self-contained JSON structure built around:

- `task_id`
- `group_id`
- `topic`
- `function_name`
- `task_description`
- `signature`
- `code_under_test`
- `risk_tags`
- `expected_test_focus`
- `hidden_reference_tests`
- `cases`

## MBPP-Sanitized Local Import (M2.0)

MBPP-Sanitized is the planned primary public experiment dataset. Its raw JSON or JSONL file must be downloaded manually and kept locally; the importer performs no network requests.

```bash
python scripts/import_mbpp.py --input datasets/raw/mbpp/mbpp_sanitized.json --output-dir datasets/processed/mbpp
```

The importer writes a unified JSONL task file and import reports. It stores official dataset tests as `hidden_reference_tests`, but its explicitly allowlisted `agent_visible_context` never contains those tests. Generated outputs and raw dataset files are ignored by Git; the synthetic fixtures are for importer tests only and are not experiment data.
