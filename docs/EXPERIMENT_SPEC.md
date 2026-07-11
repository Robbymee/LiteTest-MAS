# Experiment Specification

## Target comparison

LiteTest-MAS evaluates whether structured communication reduces message cost, whether StateVector reduces repeated context, and whether SharedMemory enables useful cross-task reuse without harming outcomes.

Formal groups are G1 Text, G2 Protocol, G3 Protocol + StateVector, and G4 Protocol + StateVector + SharedMemory.

## Required eventual metrics

- Agent message count, text character count, token count, LLM call count, and per-task duration.
- Non-text state-transfer count and data size.
- Shared-memory query count, hit rate, and effective-reuse rate.
- Test-generation success rate, executable-test-file rate, and test pass rate.
- Coverage, branch coverage, and mutation score may be added later; none are current results.

## Dataset conversion and leakage boundary

Each imported public task must retain `source_dataset`, `source_task_id`, and provenance. Its reference implementation is `code_under_test`; task description, function name, signature, and entry point may form `agent_visible_context`.

Official dataset tests are stored as `hidden_reference_tests`. They must not be included in any Agent prompt, agent-visible record, or risk-tag derivation. The first importer derives risk tags only through deterministic static inspection of task description, signature, and code.

## Reproducibility

Formal results require openEuler 24.03-LTS-SP3 x86_64 reproduction. Windows development environments, including `.venv`, are not copied to openEuler; dependencies are installed anew there.
