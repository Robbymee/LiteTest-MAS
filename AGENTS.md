# LiteTest-MAS Agent Working Rules

## Required reading before every task

Before making changes, Codex must read this file and all of the following:

- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- `docs/STATUS.md`
- `docs/EXPERIMENT_SPEC.md`
- `docs/DECISIONS.md`

It must also inspect the relevant implementation, tests, and dependency files.

## Delivery rules

- Complete exactly one milestone or clearly bounded subtask at a time. Do not begin the next stage automatically.
- Do not proceed to the next stage when the current stage fails acceptance.
- Run the applicable acceptance commands, report only their actual results, and check that existing behavior remains intact.
- Update `docs/STATUS.md` after the task. Record material technical or experimental decisions in `docs/DECISIONS.md`.
- At the end of a task, review the final goal, current stage, and remaining route; provide exactly one next step and stop.
- Never fabricate experiment, platform, benchmark, coverage, or model results.

## Experiment and portability constraints

- `hidden_reference_tests` must never be exposed to Planner, TestGen, or any other Agent prompt/context.
- Do not put Windows-only paths into core code. Use portable `pathlib` paths.
- Do not download models, configure CUDA, or modify openEuler package sources, certificates, or network settings without explicit authorization.
- Explain the necessity of every new dependency. Preserve the mock/template backend unless a separately accepted stage replaces it.
- A single task failure must not terminate a future batch experiment; it must be recorded and processing must continue.
- Formal results must be reproduced on openEuler. A Windows result is not an openEuler result.
