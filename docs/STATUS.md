# Status

## Current stage

M9.1 赛题对齐强化的 P1（赛题需求与证据矩阵）已完成 Windows 与 openEuler 验收。该阶段只审计代码、测试和 M9 公开数据，未调用真实模型，未修改 M9 正式运行、冻结提交、公开聚合、Dashboard 或发布标签。M9 的唯一有效正式基线仍为 freeze SHA `cc7aac0417afb6acab47baaf7449459692fa9444`；P1 验收时 strict verifier 仍返回 240 条 final records、零错误和零重复。

M10 is complete. The accepted formal baseline remains freeze SHA `cc7aac0417afb6acab47baaf7449459692fa9444`, recording corrected Runner implementation SHA `aeddd07c1dabb1ef18df7eac6a3c6d94866fa3e`. The offline delivery, security audit, documentation, and independent openEuler reproduction were accepted on 2026-07-13.

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
- M9 formal Spec was generated at `experiments/m9_experiment_spec.json` with 240 unique public task identities and task-plan SHA `961e83ea1abc56d762728ea6f25a5d3d07f5de7d54a98077a30068af0ff053b5`. It fixes G1-G4, seeds 42/43/44, execution order, `local-llama31-8b-instruct` over OpenAI-compatible HTTP, temperature 0, max tokens 256, timeout 300 seconds, retry 1, concurrency 1, component versions, FIFO memory limits, and bootstrap seed/resamples. Windows and openEuler strict dry-runs both reported `planned=240`, `duplicates=0`, and no model call. The openEuler dry-run log is `/home/oa/LiteTest-MAS/runs/validation/m9_spec_dry_run_openeuler-20260712-100406.log`, with `8 passed` targeted tests. The freeze commit is `6c093306ce9c8e48d051fa6371ea6e3e056a35cc`; the Spec does not include that SHA.
- The pre-`5d8b909` M9 freeze is invalidated: the full Runner path did not execute selected tasks and G2-G4 did not apply their actual communication/state/memory paths. The corrected Runner executes selected combinations sequentially, uses Text for G1, protocol messages for G2, StateVector for G3, and StateVector plus group-scoped FIFO memory for G4. Windows Mock tests passed; openEuler at `5d8b909` completed and strictly verified four 10-task MBPP Mock combinations. The follow-up `aeddd07` makes the G4 canary use the same State/Memory path, but openEuler validation is pending because Windows-to-openEuler SSH timed out after that push.
- The corrected G4 path was revalidated after SSH recovery at `06fd2b216d396d5960cf986e472145847e82f572`: Mock HumanEval+ G4 completed with parse success and valid public leakage scan; real HumanEval+ G4 completed successfully with parse success and leakage count 0. The targeted Runner/P3/Verifier regression command passed on openEuler, with `git diff --check` and a clean worktree. The log is `/home/oa/LiteTest-MAS/runs/validation/m9_corrected_g4_openeuler-20260712-144454.log`. These are acceptance canaries only, not formal experiment results.
- Replacement formal Spec was generated from corrected implementation SHA `aeddd07c1dabb1ef18df7eac6a3c6d94866fa3e` and frozen in commit `cc7aac0417afb6acab47baaf7449459692fa9444`. Its task-plan SHA remains `961e83ea1abc56d762728ea6f25a5d3d07f5de7d54a98077a30068af0ff053b5` and its Spec SHA is `5f85395ccbd8dd1bcb71e23076be42b5250d043be375d40385469e9b2c22a499`. Windows and openEuler strict dry-runs reported `planned=240`, `duplicates=0`, and no model call; the openEuler log is `/home/oa/LiteTest-MAS/runs/validation/m9_replacement_spec_openeuler-20260712-145917.log` with `7 passed` targeted regression tests. The freeze SHA remains outside the Spec.
- M9 formal execution used the replacement freeze on openEuler and produced 240 public final records. Strict verification reported `planned_count=240`, `final_count=240`, no errors, and inventory SHA `052ac73833ce6a91c7b7f3dec657b6fcd4a04959b5561eb5dfd39aa49dfbb10a`; the completion marker matches the frozen Spec and SHA. There were 168 `completed_success` records and 72 `failed_official_tests` records. All 240 parsed successfully, completed private evaluation with official metrics, and had zero infrastructure failures; 72 model-quality failures are retained as results, not reclassified as runner failures. Public recursive leakage scanning covered 242 JSON files and found zero prohibited fields. The openEuler acceptance summary is `/home/oa/m9-runs/m9_formal_ablation_v1/validation/m9_formal_openeuler_acceptance-20260713-0127.json`.
- M9 aggregation and audit used the public-only `scripts/aggregate_m9_results.py` at analysis SHA `9e0961cd590f5d70729ffe49b089d715eb041b70`, with the frozen worktree used read-only to rebuild the fixed plan. On openEuler, `8` aggregation/verifier/spec tests passed and the real 240-record aggregate passed strict verification again. The output is `/home/oa/m9-runs/m9_formal_ablation_v1/analysis/m9_aggregate_9e0961c`; it contains task/group/dataset/seed JSON and CSV, a Markdown report, and 40 paired comparison rows. Bootstrap used the frozen 2,000 resamples, 95% confidence, and seed `20260711`, pairing `(seed, dataset, task_id)`. G1/G2/G3/G4 task success rates were `0.60/0.75/0.75/0.70`; observed paired task-success differences (treatment minus control) were G2-G1 `0.15` (95% CI `0.0333` to `0.2671`), G3-G2 `0.00` (CI `-0.0833` to `0.0833`), G4-G3 `-0.05` (CI `-0.1167` to `0.0000`), and G4-G1 `0.10` (CI `0.0000` to `0.2167`). These are fixed-task, fixed-model results only.
- M10 added a standard-library offline Dashboard builder and delivery audit. The Dashboard reads only public M9 aggregate manifest, group, dataset, seed, and paired-comparison JSON; it embeds sanitized data for offline viewing and excludes task prompts, candidates, private tests, credentials, request IDs, absolute paths, and model paths. An independent openEuler clone at `97eb5012d9e20083233840e898f490fb09db6f32` passed the M10 delivery tests (`3 passed`), built a 240-record Dashboard, and passed the delivery audit with zero errors. Checksums were `fdb7d2de84b89804a5b24d85190c4f6a9285ddcdd32c6752d7754869a86b3f98` for `index.html` and `41483d40d3ee85fb2da0c180e5273457f8c135b8074376a0ac9af3357636ccdd` for `data.json`. The output is `/home/oa/m9-delivery/m10_dashboard_97eb501`.

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

- No planned milestone remains.

## Current unique next step

P1 已验收。唯一下一步是 P2：基于既有 240 条 M9 公开记录进行不调用真实 LLM 的指标补充聚合。

Maintain the tagged release; any future experiment or feature work requires a separately approved milestone.

## M9.1 P2 验收记录

P2 已完成。补充聚合脚本只读取 M9 正式运行的公开 `public/` 记录和公开聚合字段，没有调用真实 LLM，也没有读取或修改 private attempts、candidate code、raw responses、hidden tests、M9 原始运行目录、Dashboard 或发布标签。

本阶段生成了 `reports/m9/` 下的通信层、状态效率、记忆复用、数据集任务组、seed 一致性和质量开销 CSV，以及中文补充分析报告。原始公开字段可以支持的任务成功率、official-test、解析、Sandbox、总 Token、StateVector 已重新聚合；通信 Token 分层、Protocol 字节、握手、重复上下文、StateVector 等价文本与编解码耗时、Memory 门控和有效复用、总墙钟时间等无法从 M9 公开 schema 恢复的字段均保持 `unavailable`，未以零值或推测值替代。

Windows 验收：P2 专项测试 `3 passed`，全量测试 `66 passed`，`git diff --check` 通过。openEuler 24.03-LTS-SP3 验收：P2 专项测试 `3 passed`，全量测试 `65 passed, 1 skipped`，`git diff --check` 通过；跳过项为既有 Windows-only 测试。两端代码 SHA 均为 `f6ea9aad97ec9e3dd2c8eb094a6d421a2a615785`。正式 M9 freeze SHA `cc7aac0417afb6acab47baaf7449459692fa9444` 与 `v1.0.0-experiment` 未改变。

P2 验收通过。唯一下一步是 P3：按正式 manifest 对 MBPP 与 HumanEval+ 的数据集、关联任务组和失败分布进行公开字段分析；P3 开始前仍不得实现 Protocol V2、StateVector V2、SharedMemory V2 或运行 M9.1 正式实验。

## M9.1 P3 验收记录

P3 已完成。新增 `scripts/analyze_m9_task_groups.py`，从正式 `experiments/m9_experiment_spec.json` 读取真实 `dataset`、`group_id`、`task_id` 和 manifest 顺序，从 P2 已生成的公开 CSV 读取 dataset×G1-G4 指标及 G4 Memory 明细，生成 `docs/关联连续任务设计说明.md`。脚本不读取私有运行记录，不调用真实 LLM，也不修改 M9 数据。

报告覆盖 MBPP 与 HumanEval+ 的每个实验组、任务成功率、official-test 通过率、总 Token、provider latency、StateVector 次数和字节、模型质量失败与基础设施失败。两类数据集各有两个真实关联组，每组 5 个真实 task ID；连续任务顺序、Memory reset 边界和 G4 可确认的 hit/reuse task ID 均由 manifest 或公开明细生成。accept、reject、abstain、注入 Token 和 effective reuse 未被推测，继续标记为 `unavailable`。

Windows P3 专项测试 `2 passed`，全量测试 `68 passed`，`git diff --check` 通过。openEuler P3 专项测试 `2 passed`，全量测试 `67 passed, 1 skipped`，`git diff --check` 通过；两端当前 SHA 均为 `3ec3a88d3c2d6d66d95394895a5023a81d122356`，openEuler 工作区干净。P3 仍未进入 P4、Protocol V2、StateVector V2、SharedMemory V2 或 M9.1 正式实验。

P3 验收通过。唯一下一步是 P4：基于公开 task-level 记录开展 seed 相关性与 task-cluster Bootstrap 敏感性分析，固定 `bootstrap_seed=20260711` 和 `bootstrap_resamples=2000`。

## M9.1 P4 验收记录

P4 已完成。`scripts/analyze_m9_seed_sensitivity.py` 只读取正式 M9 的 `public/tasks` 和既有公开普通配对比较文件，新增 `seed_correlation_summary.csv`、`task_cluster_bootstrap.csv`、`seed_sensitivity_manifest.json` 与中文 `reports/m9/随机种子相关性分析.md`。它没有修改 M9 原始聚合、正式记录、冻结 SHA、Dashboard 或发布标签，也没有调用真实 LLM。

在所有 dataset×G1-G4 单元中，三个 seed 的 candidate SHA、任务成功状态、official-test 全通过状态和总 Token 完全重复率均为 `1.0`。因此 task-cluster Bootstrap 使用 `dataset + task_id` 作为重采样单位，每个聚类包含 3 个 seed。普通 CI 保留不替换；任务成功率的聚类 CI 分别为 G2-G1 `[-0.05, 0.35]`、G3-G2 `[-0.15, 0.15]`、G4-G3 `[-0.15, 0.0]`、G4-G1 `[-0.1, 0.3]`。它们相对普通 CI 更宽，说明本次 temperature=0 运行的三 seed 高度相关，普通 CI 的独立观测解释应保持谨慎。

Windows P4 专项测试 `2 passed`，全量测试 `70 passed`，`git diff --check` 通过。openEuler P4 专项测试 `2 passed`，全量测试 `69 passed, 1 skipped`，`git diff --check` 通过，工作区干净。P4 未进入 Protocol V2、StateVector V2、SharedMemory V2 或 M9.1 正式实验。

P4 验收通过。唯一下一步是 P5：在独立模块中实现 `compact_protocol_v2`，并使用合成 fixtures 与 Mock Backend 完成单元测试；不得修改 `protocol_v1` 语义或运行 M9.1 正式实验。

## M9.1 P5 验收记录

P5 已完成。新增独立 `protocol/compact_v2.py`、`capability_registry.py`、`reference_registry.py` 和 `protocol_metrics.py`，以及中文设计文档 `docs/结构化通信协议设计.md`。V2 支持一次握手、能力发现与协议映射、task/reference registry、状态和记忆 ID、稳定序列化、默认字段省略、版本拒绝和通信字节统计；未修改 `protocol_v1`、`ProtocolAdapter`、Text Mode 或 M9 Runner。

Windows P5 专项测试 `6 passed`，全量测试 `73 passed`，`git diff --check` 通过。openEuler P5 专项测试 `6 passed`，全量测试 `72 passed, 1 skipped`，`git diff --check` 通过。两端代码 SHA 为 `a2ca0edc09117e3b9f5192426f4c1f57790a1de0`，openEuler 工作区干净。测试使用合成 fixtures，未调用真实 LLM、未运行 M9.1 正式实验；私有字段拒绝测试通过。

P5 验收通过。唯一下一步是 P6：实现独立 `state_vector_v2`，以确定性 bytes 替代重复文本状态，并先完成合成 fixtures 的跨平台测试。

## M9.1 P6 验收记录

P6 已完成。新增独立 `state/vector_v2.py` 和中文设计文档 `docs/非文本状态传递设计.md`。V2 使用标准库 `struct`、网络字节序和固定 33 字节布局，包含版本、phase、source/target role、progress、artifact flags、error、retry、confidence、state reference 和 memory reference count；支持生成、编码、传递、校验、解码、等价文本字节数和压缩率计算。现有 `state/vector.py` V1 未修改。

Windows P6 专项测试 `4 passed`，全量测试 `76 passed`，`git diff --check` 通过。openEuler P6 专项测试 `4 passed`，全量测试 `75 passed, 1 skipped`，`git diff --check` 通过。两端代码 SHA 为 `af8999a`，openEuler 工作区干净。P6 使用合成 fixtures，未调用真实 LLM、未接入正式 Runner、未运行 M9.1 正式实验。

P6 验收通过。唯一下一步是 P7：实现独立 `gated_shared_memory_v2`，加入成功门控、隔离、阈值、top_k、预算和 abstain，并先完成合成测试。

## M9.1 P7 验收记录

P7 已完成。新增独立 `memory/gated_shared_memory_v2.py` 和中文设计文档 `docs/共享记忆设计与门控策略.md`。V2 支持完整记忆元数据、success-only 默认门控、失败经验标记、dataset/task_group/seed/experiment 隔离、轻量相关性评分、固定 `top_k`、relevance/confidence threshold、token budget、主动 abstain、reuse/effective reuse、eviction 和敏感字段拒绝；现有 `memory/shared_memory.py` V1 未修改。

Windows P7 专项测试 `5 passed`，全量测试 `79 passed`，`git diff --check` 通过。openEuler P7 专项测试 `5 passed`，全量测试 `78 passed, 1 skipped`，`git diff --check` 通过。两端代码 SHA 为 `c5b971e`，openEuler 工作区干净。P7 使用合成 fixtures，未调用真实 LLM、未接入正式 Runner、未运行 M9.1 正式实验。

P7 验收通过。唯一下一步是 P8：补充真实多 Agent 逻辑角色与协作链证据，并说明逻辑角色和 LLM 调用次数的区别；不得虚构独立 Agent。

## M9.1 P8 验收记录

P8 已完成。新增 `agents/collaboration.py`，并在既有 Runtime 生成 `agent_collaboration.json`，记录 `role_id`、`capability_id`、`action`、`input_reference`、`output_reference`、`started_at`、`completed_at` 和 `status`。证据覆盖 Planner、Retriever/Memory、TestGen、Executor 和 Summarizer 五类逻辑职责；未知 sender 会显式标记为 `unmapped`，不会被虚构成 Agent。

文档明确：当前 MemoryAgent 是确定性上下文存储，并非独立 LLM Retriever；逻辑角色事件不等于 LLM 调用次数。M10 Dashboard 属于冻结发布产物，本阶段未覆盖或改写，只保留新增角色 JSON 和中文流程文档。

Windows P8 专项测试 `5 passed`，全量测试 `81 passed`，`git diff --check` 通过。openEuler P8 专项测试 `5 passed`，全量测试 `80 passed, 1 skipped`，`git diff --check` 通过。两端代码 SHA 为 `a2b92a2`，openEuler 工作区干净。

P8 验收通过。唯一下一步是 P9：生成独立 M9.1 Spec 并完成正式运行前的测试、canary、泄漏和冻结门槛；不得把 M9 结果复制为 M9.1 结果。

## M9.1 P9.1 Spec 验收记录

P9.1 已完成。新增 `experiments/m9_1/spec.json`、Spec 生成脚本和中文说明。Spec 使用真实 M9 manifest 的 240 个公开 task ID 和固定顺序，映射为独立 S1-S4，固定 `result_scope=supplementary_competition_alignment_ablation`、`conclusion_scope=fixed_task_fixed_model_supplementary_analysis`，并声明 CompactProtocol V2、StateVector V2 和 GatedSharedMemory V2。

M9.1 Spec 保留 M9 的模型、数据集、任务、seed、temperature、timeout、retry、max_tokens、Parser、Sandbox 和评测边界；正式规模为 240 条。当前 Spec 的 `implementation_git_sha` 固定为 P8 完成 SHA，Spec 提交 SHA 为 `45ad79b`；这不是正式实验 freeze SHA。M9 原 Spec、M9 结果、Dashboard 和 `v1.0.0-experiment` 未修改。

Windows P9.1 Spec 专项测试 `3 passed`，全量测试 `83 passed`，`git diff --check` 通过。openEuler Spec 专项测试 `3 passed`，M9 Spec 回归通过，全量测试 `82 passed, 1 skipped`，`git diff --check` 通过，工作区干净。尚未调用真实 LLM，尚未运行 M9.1 canary 或正式实验。

P9.1 验收通过。唯一下一步是 P9.2：在独立 M9.1 Runner/Verifier 门槛上完成 fake canary、两项真实 canary、public leakage=0 和 freeze SHA 校验；未通过前不得启动 240 条正式运行。

## M9.1 P9.2 Preflight 验收记录

## M9.1 P9.3 S 组 Runner 语义记录

## M9.1 P9.4 真实 Canary 记录

## M9.1 P9.5 Canary 审计与 Freeze 记录

P9.5 已完成。新增 `scripts/audit_m9_1_canary.py`，在 openEuler 对两条 `m9_1_real_canary` 公开 JSON 完成字段、scope、绝对路径、凭据和敏感字段审计：`valid=true`、`record_count=2`、错误数为 0。两项 `task_success=false` 仍被保留，`infrastructure_failure` 未由 canary 记录推断，保持 `unavailable`。

M9.1 Spec 的 `implementation_git_sha` 已校正为真实 V2 canary 运行链提交 `0c1782e705e261a91748cee59aa06a9922fb70f6`。包含 Spec 校正、canary 审计代码并已在 openEuler 完成审计的 freeze 候选 SHA 为 `e5f3777`；freeze SHA 不写入 Spec 自身，正式运行必须明确 checkout 该 SHA。

Windows P9.5 审计专项测试 `2 passed`，Spec/preflight 测试 `4 passed`，`git diff --check` 通过。openEuler 审计专项测试 `4 passed`，真实 canary 审计 `valid=true`，`git diff --check` 通过，工作区干净。正式 240 条 M9.1 运行尚未启动。

P9.5 验收通过。唯一下一步是 P9.6：在 freeze SHA `e5f3777` 上完成正式运行前最终门槛复核，然后才可启动 S1-S4 的 240 条 M9.1 正式实验。

## M9.1 P9.6 最终运行前门槛

## M9.1 P9.7 启动安全检查

P9.7 未启动正式实验。无模型 dry-run 已确认 Spec 计划为 `240` 条、scope 为 `supplementary_competition_alignment_ablation`、实验组为 S1-S4；openEuler 当前不存在 `runs/m9_1/completion.json`。

检查 freeze `e5f3777` 发现独立 Runner 当前只有单项 `execute_canary`，尚未实现 240 条批量执行、Checkpoint/Resume、逐条失败继续、Strict Verifier 和正式 completion marker。直接运行会产生不符合 M9.1 验收定义的结果，因此本阶段主动停止，未调用模型、未写入正式 runs、未复制 M9 结果。

P9.7 启动检查未通过，但原因已明确且可修复。唯一下一步是 P9.7a：补齐独立 M9.1 批量 Runner、Checkpoint/Resume、Strict Verifier 和正式 completion marker，再重新执行启动门槛。

## M9.1 P9.7a 批量 Runner 框架

P9.7a 已完成独立批量框架：`experiments/m9_1_runner.py` 新增 `run_batch`、稳定 checkpoint key、resume 跳过和逐任务异常记录；`scripts/run_m9_1_experiment.py` 默认 dry-run，正式执行必须显式指定 `--freeze-git-sha e5f3777`。Windows/openEuler dry-run 都返回 `planned=240`、`completed=0`，未调用模型。

Windows P9.7a 全量测试 `89 passed`，openEuler P9.7a 全量测试 `88 passed, 1 skipped`，`git diff --check` 通过。当前框架尚未实现正式公开结果目录、M9.1 Strict Verifier 和 completion marker；因此仍不得执行 240 条正式实验。

P9.7a 部分验收通过。唯一下一步是 P9.7b：定义 M9.1 公共结果 schema、Strict Verifier 和 completion marker，并以合成记录验证 Checkpoint/Resume 与逐条失败继续。

## M9.1 P9.7c 公共结果协议接通

P9.7c 已完成。批量 Runner 现在将每条公开结果写入独立 `public/tasks/`，包含 S 组配置、result scope、freeze SHA、implementation SHA、final status 和公开质量字段；240 条均完成后才由 M9.1 Strict Verifier 写入 completion marker。合成 240 条记录、缺失/重复拒绝、checkpoint/resume 和 dry-run 均通过测试。

Windows P9.7c 全量测试 `91 passed`，openEuler P9.7c 全量测试 `90 passed, 1 skipped`，`git diff --check` 通过。该运行代码提交为 `017c2fb`，因此旧 freeze `e5f3777` 不再包含完整正式 Runner/Verifier，已不适用于 M9.1 正式运行；M9 不受影响，正式 M9.1 仍未启动。

P9.7c 验收通过。唯一下一步是 P9.8：从完整 Runner/Verifier 实现生成新的 M9.1 Spec、重新冻结并重新执行运行前门槛；旧 freeze 不得用于正式实验。

P9.6 已完成。Spec Verifier 返回 `valid=true`，任务计划为 240 条且 S1-S4 identity 唯一；freeze 候选 `e5f3777` 存在，M9.1 Spec 的 implementation SHA 与 V2 canary 运行链一致。当前 HEAD 相对 freeze 候选只增加 `docs/STATUS.md` 和 `docs/DECISIONS.md`，没有改变 M9.1 运行代码或 Spec；正式运行必须 checkout `e5f3777`。

M9 `v1.0.0-experiment` 标签和正式结果未改变。Windows/openEuler 的 P9.4 全量回归分别为 `86 passed`、`85 passed, 1 skipped`；P9.5 openEuler canary 审计为 `valid=true`、2 条记录、泄漏错误 0。P9.6 未调用模型，未创建 M9.1 正式完成标记。

P9.6 验收通过。唯一下一步是 P9.7：在 freeze SHA `e5f3777` 上启动并完成 M9.1 S1-S4 的 240 条正式实验，使用独立 `runs/m9_1/`，不得覆盖 M9 运行目录或结果。

P9.4 已接入真实 Backend canary 运行链：S1 保持 Text，S2 使用 CompactProtocol V2，S3 增加 StateVector V2，S4 增加 GatedSharedMemory V2；输出范围独立为 `m9_1_real_canary`，运行目录为被 Git 忽略的 `runs/m9_1_canary`，未创建正式完成标记。

已执行两项真实 canary：S2 + MBPP `mbpp_sanitized:591`，S4 + HumanEval+ `humaneval_plus:HumanEval/27`。两项都完成了 Backend 请求和私有评测流程，但 `task_success=false`；这是本次固定模型 canary 的真实质量结果，未被改写为基础设施失败或成功。正式 M9.1 仍未启动。

Windows P9.4 全量测试 `86 passed`，openEuler P9.4 全量测试 `85 passed, 1 skipped`，`git diff --check` 通过，两端当前 SHA 为 `0c1782e`。P9.4 尚未完成独立 canary 记录的最终 leakage 扫描、freeze SHA 绑定和两项 canary 的正式验收报告。唯一下一步是 P9.5：完成真实 canary 公开字段/泄漏审计、freeze SHA 校验和正式运行前最终门槛。

P9.3 已完成 S1-S4 计划和配置语义的独立实现：新增 `experiments/m9_1_runner.py`、`scripts/run_m9_1_canary.py` 和对应测试。Runner 不复用 M9 的 G1-G4 group 配置；S1-S4 的 component、mode、StateVector 和 Memory 开关均从 M9.1 Spec 读取。S2 Mock canary 在 Windows/openEuler 均输出 `result_scope=m9_1_runner_canary`、`component=compact_protocol_v2` 和 `model_call=false`。

Windows P9.3 专项测试 `3 passed`，全量测试 `86 passed`，`git diff --check` 通过。openEuler P9.3 专项测试 `3 passed`，全量测试 `85 passed, 1 skipped`，`git diff --check` 通过，工作区干净。当前提交 SHA 为 `06b1c4f`。

本阶段只完成 S 组计划/配置和 Mock canary 语义，未调用真实模型，未完成两项真实 canary，未声明 public leakage=0 或 freeze SHA 正式运行门槛通过。唯一下一步是 P9.4：接入真实 Backend、V2 Prompt/Protocol/State/Memory 运行路径并完成两项真实 canary。

P9.2 的独立 Spec Verifier 和 fake canary 门槛已完成。新增 `scripts/verify_m9_1_spec.py` 与 `scripts/run_m9_1_fake_canary.py`，校验 S1-S4、240 条计划、唯一 task identity、plan index、公开泄漏字段、独立 result scope 和 fake scope；fake canary 不调用模型，也不能冒充正式 supplementary 结果。

Windows P9.2 专项测试 `4 passed`，全量测试 `85 passed`，`git diff --check` 通过。openEuler P9.2 专项测试 `4 passed`，全量测试 `84 passed, 1 skipped`，`git diff --check` 通过，工作区干净。当前提交 SHA 为 `ed160a2`。

真实 canary 尚未执行，public leakage=0 与 freeze SHA 运行门槛尚未宣称通过；原因是现有 M9 Runner 的 group 语义固定为 G1-G4，尚不能安全执行 S1-S4。P9.2 Preflight 部分验收通过。唯一下一步是 P9.3：实现独立 M9.1 Runner/Verifier 的 S1-S4 执行语义，然后再执行两项真实 canary。

## M9.1 P9.8 批量运行加固

P9.8 已在 Windows 完成批量运行链加固。独立 Runner 现在为每条公开记录写入完整的通信、模型、StateVector、Memory、质量和耗时指标字段：可直接观测的值按实际运行记录，无法由单条公开记录可靠得到的值统一写为 `unavailable`，不以 `0` 或推测替代。基础设施异常仍会写入脱敏的 `failed_infrastructure` 最终记录，批次继续执行；公开记录采用临时文件替换，completion marker 仅在 240 条规范路径记录均存在时写入。

连续任务的 `compact_protocol_v2` 会话按 dataset、任务组、seed 和实验组复用，握手只在该 sequence 的首条任务中发出并计入通信指标；后续任务复用 capability registry。S4 Memory 保持 dataset、任务组、seed 和 experiment ID 隔离，并记录实际的检索、门控、注入和复用计数。CLI 正式运行仍要求显式 `--freeze-git-sha`，且当前 `HEAD` 必须与该 SHA 严格一致。M9 原始结果、`reports/m9`、Dashboard、冻结 SHA `cc7aac0417afb6acab47baaf7449459692fa9444` 和标签 `v1.0.0-experiment` 均未修改；未调用真实模型，未创建 M9.1 freeze，未运行正式 240 条任务。

Windows 专项回归为 `19 passed`，全量测试为 `93 passed`，`git diff --check` 通过。openEuler 在同一实现 SHA `b529dc1177e94526f41bb6049e6d280fcd56b46f` 上通过专项 `19 passed`、全量 `92 passed, 1 skipped` 和 `git diff --check`；由于该机无法解析 `github.com`，代码以 Windows 已验证的 Git bundle 执行 `git pull --ff-only` 同步，未更改 DNS、远程配置或历史。openEuler mock dry-run 返回 `planned=240`、`completed=0`，没有调用模型，也没有生成 completion marker。P9.8 验收通过，旧 freeze `e5f3777` 继续禁止用于 M9.1 正式运行。

唯一下一步是：生成与 P9.8 完整 Runner/Verifier 实现一致的新 M9.1 Spec，完成双平台 Spec/泄漏门槛后创建新的 freeze 候选；不得启动正式 240 条实验。

## M9.1 P9.9 Spec 重建与冻结前门槛

P9.9 已在 Windows 重建独立 `experiments/m9_1/spec.json`，将 `implementation_git_sha` 从过期的 V2 canary 链 SHA 更新为 P9.8 已验收 Runner/Verifier 实现 SHA `b529dc1177e94526f41bb6049e6d280fcd56b46f`。除此之外，M9.1 的 240 条真实公开任务身份与顺序、S1-S4、模型、seed、生成参数、Parser、Sandbox、Memory 阈值、Bootstrap 参数、`result_scope` 和 `conclusion_scope` 均未改变。任务计划 SHA 仍为 `c1b4ef24773480b9cd55ab2f774465a6b32955f62d0c0eefe0e4d5c4bf03db4b`，当前 Spec 文件 SHA256 为 `7ff97f159a5c9b0754169d3839595457cb0e6a217e584848479dd9c22e9a9064`。

新增一致性测试保证已提交 Spec 可由固定 M9 公开计划、当前构建器和 Spec 自身声明的 implementation SHA 确定性重建。Windows P9.9 专项测试 `13 passed`、全量测试 `94 passed`，Spec Verifier 返回 `valid=true`、240 条计划、零错误，递归禁用字段检查通过，`git diff --check` 通过。文本扫描命中的 `candidate_codegen_v1` 是公开组件版本值，不是 `candidate_code` 字段或候选代码泄漏。

openEuler P9.9 验收尚未执行，因此本阶段尚未完成。当前 Spec 提交也不是 freeze SHA，未创建 freeze 候选、未调用真实模型、未运行正式 240 条实验；旧 freeze `e5f3777` 继续禁止使用。

唯一下一步是：提交 P9.9 Spec 补丁并在 openEuler 同一 SHA 上执行专项、全量、Spec Verifier、公开字段检查和 mock dry-run；全部通过后才能创建新的 freeze 候选。
