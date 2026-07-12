# Decisions

1. Use a lightweight in-house system; do not heavily fork AutoCodeAI.
2. Use AutoCodeAI only as a reference for Agent, sandbox, and memory modules.
3. MBPP-Sanitized is the primary experiment dataset.
4. HumanEval is the external-validation dataset.
5. Hand-authored tasks such as A01 are smoke tests only.
6. Preserve mock/template Agents at the current stage.
7. The first SharedMemory implementation is planned to use SQLite.
8. The first StateVector may use a deterministic hash vector.
9. Replace that vector with real embeddings only in a later stage.
10. Reproduce all formal results on openEuler.
11. Do not copy a Windows `.venv` to openEuler.
12. Reinstall dependencies on openEuler.
13. M2.0 imports only user-provided local MBPP-Sanitized files; it never downloads data or changes network/certificate configuration.
14. The M2.0 importer stores official tests separately and constructs agent-visible context from an explicit allowlist.
15. With explicit authorization on 2026-07-11, MBPP-Sanitized is sourced from Google Research and HumanEval+ v0.1.10 from EvalPlus; raw releases remain local and Git-ignored.
16. Candidate manifests contain only static agent-visible metadata. Deterministic recommendations are not final experiment selections and require human confirmation.
17. The automatic `list` and `empty_input` recommendations were rejected: risk-tag co-occurrence does not establish a continuous-task relationship.
18. The fixed, human-approved primary MBPP sequences are `mbpp_list_rearrangement` (591, 644, 586, 743, 632) and `mbpp_regex_string_matching` (434, 285, 787, 794, 607), in the recorded order.
19. Selection requires semantic relatedness, reusable testing knowledge, non-duplicative tasks, and coverage of distinct task types. The selection manifest never exposes hidden tests and must not be changed in response to experiment outcomes.
20. M2.2 runs the two approved groups as isolated sequences of five rounds each, for ten rounds per mode. Manifest order is authoritative; Text and Protocol share the task plan but do not share Agent instances, messages, or state.
21. M2.2 has no cross-task long-term memory or StateVector. Hidden tests remain outside agent views and all `runs/` artifacts remain untracked.
22. `task_plan_sha256` hashes the mode-independent task plan; `deterministic_result_sha256` hashes only safe logical round results and excludes timestamps, absolute paths, and machine-specific fields. M2.2 is a runner-completeness stage, not formal metric comparison.
23. M2.3 uses HumanEval+ v0.1.10 as the external-validation source. Its canonical solution remains local `code_under_test` only; agent-visible context excludes reference implementations, official tests, contracts, and inputs.
24. M3 Evaluator is independent and read-only. It reports `mock_validation` only, uses white-listed output fields, and distinguishes unavailable metrics from zero.
25. Deterministic evaluation paths are repository-relative POSIX strings; absolute paths, usernames, hostnames, timestamps, and output directories do not affect input or deterministic evaluation hashes.
26. M4 defines a model-independent synchronous Backend interface with deterministic Mock and OpenAI-compatible implementations. Unknown backends never silently fall back to Mock; provider usage absent from a response remains unavailable.
27. OpenAI-compatible configuration is environment-driven, defaults to SSL verification, uses bounded retry categories, and redacts API keys. M4 performs dry-run validation only; M5 is required for any real request and openEuler must not host a large local model.
28. M5 serves the Windows-local Llama 3.1 8B Instruct Safetensors snapshot through a lightweight Transformers/FastAPI OpenAI-compatible service. Snapshot resolution is supplied at runtime; no snapshot hash or Windows absolute path is committed. The service uses local files only, non-streaming generation, inference mode, and a single generation lock.
29. openEuler invokes the Windows service only over the firewall-restricted HTTP address `172.24.64.1:8000`; it never loads the model, uses Ollama, or calls a remote model API. Requests use `temperature=0`, seed `42`, timeout 300 seconds, at most one retry, and concurrency one.
30. M5 records only white-listed task identity, request, usage, latency, status, and error metadata. Prompt construction is from the approved `agent_visible_context` allowlist and rejects hidden tests, canonical/reference solutions, official tests, contracts, credentials, and authorization fields.
31. M5 results are `real_llm_pilot` with conclusion scope `integration_and_runtime_validation_only`. The successful 2-task pilot and fixed 10-round validation establish service/backend integration only; they are not M9 formal ablation or model-quality conclusions.
32. M6 uses a deterministic in-memory FIFO SharedMemory rather than an external service. Each instance is constructed for one dataset/group/seed scope, defaults to 32 records and 8192 serialized bytes, rejects prohibited fields before persistence, and is reset/closed at group boundaries. These limits are frozen before M9.
33. M7 StateVector is a compact, explicitly enumerated JSON state record capped at 512 bytes. It carries lifecycle metadata and safe memory IDs only, never arbitrary prompt text, hidden evaluation material, answers, credentials, or paths.
34. M8 evaluates candidate code only in a temporary-directory child process with `shell=False` and Python isolation. It returns counts and error categories only; it never writes private test source or assertion values into prompts, StateVector, SharedMemory, public traces, or reports.
35. M9 Readiness freezes `candidate_codegen_v1` and `candidate_parser_v1`. The prompt is built solely from agent-visible task fields; private tests enter only after candidate generation in the ignored private Sandbox workspace. The 10-task readiness preflight is not part of formal M9.
36. The pre-`7e74d29` readiness outputs are retained but invalidated because the private adapter did not reliably load candidates under `python -I` and did not invoke HumanEval's private check. Readiness v2 is the only valid gate result for M9.
37. M9 strict verification derives expected work exclusively from a validated Spec and identifies a task by `(seed, experiment_group, dataset, task_id)`. A full public run is complete only when its Spec-derived inventory and atomic completion marker agree; the marker contains only public identity and checksum metadata. P2 validation uses synthetic public records and is not a formal experiment result.
38. M9 P3 uses an independent `m9_runner_canary` result scope for fixed MBPP G1 and HumanEval+ G4 integration checks. Canary records may end in `completed_success` or `failed_official_tests`; the hard gate is successful request, parsing, private evaluation, public-record completion, and leakage verification. Canary outputs never satisfy or create the formal M9 completion marker.
39. The formal M9 Spec is frozen from implementation SHA `d2337d48b835aeb1dba18853d1bb09f121636c27` in freeze commit `6c093306ce9c8e48d051fa6371ea6e3e056a35cc`. The freeze SHA is intentionally kept outside `experiments/m9_experiment_spec.json` to avoid self-reference; formal execution must use the freeze commit and the frozen Spec unchanged.
