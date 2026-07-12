# Status

## Current stage

M9 P3 Runner acceptance completed on 2026-07-12. The formal specification and freeze are next; no formal 240-task experiment has started.

## Completed

- M1 minimum A01 Text/Protocol mock closed loop.
- M2.0 local MBPP-Sanitized offline importer, management documents, Windows/openEuler acceptance.
- M2.1 human-approved MBPP selection manifest: two ordered groups of five tasks, ten tasks total.
- M2.2 deterministic Mock-Agent sequence runner for the fixed manifest. Text and Protocol each complete two isolated sequences of five rounds, ten rounds per mode.
- M2.3 HumanEval+ v0.1.10 local import: 164/164 records convert with zero errors on Windows and openEuler. Agent-visible context excludes canonical solutions, reference implementations, official tests, contracts, and test inputs.
- M2.4 delegated technical review generated 164 safe candidates, three double-group review schemes, and a fixed two-group selection with ten unique tasks. The manifests contain only public metadata and no hidden evaluation fields.
- M2.5 used the shared deterministic Runner for MBPP-Sanitized Text/Protocol and HumanEval+ Text/Protocol. Each of the four combinations completed 10/10 rounds with zero failures and skips on Windows and openEuler; no formal performance claim is made.
- M3 strict evaluation discovered all four Mock combinations and produced JSON, CSV, and Markdown aggregates. Windows and openEuler evaluation input hash `3b0e32b25ff312f77fb85408dd069bf29bcd556c3255b0d584b4309bb0034215` and deterministic evaluation hash `acbc2de8c44feb0dad4d2b5cc9b4fd5177277f09ac0ddca443d032261ffcb42d` match after POSIX path normalization. Actual/estimated tokens, timing, memory, SharedMemory, and StateVector remain explicitly unavailable.
- M4 added deterministic MockLLMBackend and standard-library OpenAI-compatible Backend abstractions. Windows/openEuler backend tests `3 passed` and full tests `32 passed`; OpenAI-compatible dry-run redacted the placeholder key and made no network request.
- M5 added a local-only Transformers OpenAI-compatible service for Windows, plus a safe real-LLM validation runner. Windows hosted public model name `local-llama31-8b-instruct` at `172.24.64.1:8000`; openEuler used only HTTP and did not load model weights. `/health`, curl chat, and an `OpenAICompatibleBackend` request succeeded. The fixed MBPP first task and HumanEval+ first task pilot both succeeded (2/2); the first approved group of each dataset completed in fixed order (10/10, failed 0, skipped 0). Records are `real_llm_pilot` with conclusion scope `integration_and_runtime_validation_only`, not a formal ablation.
- M6 added bounded in-process FIFO SharedMemory with explicit disabled state, dataset/group/seed instance scope, byte and record limits, stable trace serialization, reset, metrics, and prohibited-content rejection. Revalidated openEuler pilot completed 2/2 and fixed MBPP group 5/5; group trace recorded 5 writes, 4 hits, and 10 reuse references. Scope is `real_llm_memory_pilot`, not a formal ablation.
- M7 added a schema-validated StateVector with fixed enums, stable JSON, 512-byte cap, prohibited-content rejection, and optional real Runner metrics. openEuler HumanEval+ pilot 1/1 and fixed group 5/5 succeeded with 5 valid vectors (1685 bytes) and no invalid vectors; scope is `real_llm_state_pilot`.
- M8 added a fixed candidate-code extractor and isolated `python -I` subprocess evaluator with timeout and bounded output accounting. Synthetic normal, syntax-error, and infinite-loop fixtures passed on both platforms. It is explicitly a restricted subprocess sandbox, not a container security boundary.
- M9 Readiness Gate added a public-only candidate-code prompt, frozen parser `candidate_parser_v1`, and private official-test subprocess path. The real two-task pilot and fixed ten-task preflight produced final records with official metrics available for every task. All ten preflight candidates parsed but failed official tests; this is honestly recorded as model quality failure, not infrastructure completion. Public results passed leakage scan.
- M9 Readiness v2 reran after private adapter semantic fixes. The old readiness remains retained but invalidated. The v2 pilot/preflight produced 12 final records, all parse-success and official-metric-available; private official tests were 23/24 passed and task success was 11/12, with one official-test failure. This is still not formal M9.
- M9 P2 completed the strict public-run verifier. It derives the fixed 240-task plan, or a selected 10-task combination, only from a validated Spec; validates composite task identity, plan order and G1-G4 mode mapping, complete public schema, public inventory checksums, identity fields, forbidden fields, and a full-run completion marker. P2 acceptance uses only synthetic public records and the fake Spec, makes no model call, and reads no private tests. Windows M9 tests and the full test suite passed. On openEuler 24.03-LTS-SP3 / Python 3.11.6 at `2208c3d36e8210eff7c6dcf862250960840e6f9e`, M9 tests were `7 passed` and the full repository suite was `47 passed, 1 skipped`; `git diff --check` passed. The openEuler log is `/home/oa/LiteTest-MAS/runs/validation/m9_p2_verifier_openeuler-20260712-092336.log`.
- M9 P3 completed at implementation SHA `d2337d48b835aeb1dba18853d1bb09f121636c27`. Runner recovery now preserves running public metadata and historical attempts, increments `resume_count`, and skips backend calls for final records. The independent canary runner/verifier uses result scope `m9_runner_canary` and never creates a formal completion marker. Windows fake canary and full tests passed. On openEuler, fake canary verification passed; `/health`, `/v1/models`, and an OpenAI-compatible warmup passed; fixed MBPP G1 (`mbpp_sanitized:591`) and HumanEval+ G4 (`humaneval_plus:HumanEval/27`) real canaries both parsed successfully, completed successfully, and passed canary verification with leakage count 0. The openEuler full suite was `50 passed, 1 skipped`, and `git diff --check` passed. The final validation log is `/home/oa/LiteTest-MAS/runs/validation/m9_p3_runner_openeuler-20260712-095208.log`. These are runner integration canaries, not formal M9 results.

## M5 validation

- Validation code SHA: `d69f2e63614c9a60e7f4440f21a139b0140aec4a`.
- Windows: full repository tests `34 passed`; local endpoint tests use fake tokenizer/model only. The real local service was loaded from an operator-supplied snapshot path using `local_files_only=True`.
- openEuler 24.03-LTS-SP3 / Python 3.11.6: full repository tests `33 passed, 1 skipped`. The skipped test is explicitly the Windows-only FastAPI endpoint test; openEuler neither installs the local service stack nor loads the 8B model.
- Real request configuration: OpenAI-compatible HTTP, `temperature=0`, seed `42`, `max_tokens=256`, timeout `300` seconds, `max_retries=1`, single concurrency, non-streaming.
- Fixed 10-round result: succeeded `10`, failed `0`, skipped `0`; provider usage prompt/completion/total `1440/2560/4000`; mean/max recorded latency `6.200/6.342` seconds. All ten records had provider usage available.
- Leakage scan across pilot and 10-round public JSON/JSONL records found `0` matches for prohibited evaluation, credential, or absolute-path fields. Runs and validation logs remain Git-ignored.
- openEuler acceptance log: `/home/oa/LiteTest-MAS/runs/validation/m5_openeuler-20260711-074049.log`.

## M2.2 validation

- Windows: sequence-runner tests `7 passed`; full repository tests `25 passed`; Text and Protocol each completed 10/10 rounds with zero failures and skips.
- openEuler 24.03-LTS-SP3 / Python 3.11.6: sequence-runner tests `7 passed`; full repository tests `25 passed`; Text and Protocol each completed 10/10 rounds with zero failures and skips.
- Shared task-plan hash: `e3bdc4b5dd6b7501f09ae1c9848db15dce590e7edff7e7399d06b54fa80ff6a2`.
- Text deterministic result hash: `2ed1095ac8283f29f3d0ff1e0dfe88ef6fb8e702e187f358f9317cf7892afc8f`.
- Protocol deterministic result hash: `329c87684415f67fdabeca9e0ec9cb4e0b7ee9f734cf8ceff522ec51ea936fc2`.
- Runner validation commit: `c275a15cd71e76a52ce9fa551916541f410320b5`; openEuler log: `/home/oa/LiteTest-MAS/runs/validation/m2_2_openeuler-20260711-105126.log`.

## M2.3 validation

- Windows: HumanEval+ strict import 164/164 with zero errors; importer tests `2 passed`; full repository tests `27 passed`.
- openEuler 24.03-LTS-SP3 / Python 3.11.6 reproduced strict import 164/164 with zero errors, importer tests `2 passed`, full repository tests `27 passed`, and `git diff --check` passed.
- openEuler log: `/home/oa/LiteTest-MAS/runs/validation/m2_3_openeuler-20260711-110801.log`.

## Boundaries still not completed

- SharedMemory, StateVector, test-quality evaluation, ablations, and Dashboard.

## Current unique next step

M9: create and freeze the formal ablation specification after reviewing the completed P3 evidence.
