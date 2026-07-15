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
