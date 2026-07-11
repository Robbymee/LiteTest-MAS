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
