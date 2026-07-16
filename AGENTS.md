# LiteTest-MAS Agent 工作规则

## 每项任务前的必读内容

修改前必须阅读本文件以及 `docs/PROJECT_CONTEXT.md`、`docs/ROADMAP.md`、`docs/STATUS.md`、`docs/EXPERIMENT_SPEC.md` 和 `docs/DECISIONS.md`，并检查相关实现、测试和依赖文件。

## 交付规则

- 一次只完成一个里程碑或边界清晰的子任务；当前阶段未验收不得进入下一阶段。
- 运行适用验收命令，只报告实际结果，并确认既有行为未退化。
- 任务完成后更新 `docs/STATUS.md`，重要技术或实验决定写入 `docs/DECISIONS.md`。
- 结束时复核最终目标、当前阶段和剩余路线，只给出一个下一步。
- 不得虚构实验、平台、基准、覆盖率或模型结果。

## 实验与可移植性约束

- `hidden_reference_tests` 绝不进入 Planner、TestGen 或其他 Agent 的 Prompt 或上下文。
- 核心代码使用可移植的 `pathlib`，不得写入 Windows 专用路径。
- 未获明确授权，不下载模型、不配置 CUDA、不修改 openEuler 软件源、证书或网络设置。
- 每个新依赖都必须说明必要性；保留 Mock/template backend，除非独立阶段验收替换。
- 单个任务失败必须记录并继续后续批次，不能中止整个实验。
- 正式结果必须在 openEuler 复现；Windows 结果不等同于 openEuler 结果。
