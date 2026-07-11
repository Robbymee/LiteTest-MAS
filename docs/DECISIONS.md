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
