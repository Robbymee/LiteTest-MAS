# LiteTest-MAS：轻量多智能体协作实验平台

## 项目简介

LiteTest-MAS 是面向代码任务生成、测试执行与私有评测的轻量多智能体协作实验平台。系统使用 Planner、Retriever、Executor、Summarizer 等逻辑角色组织公开任务上下文，并通过结构化通信、StateVector 和 SharedMemory 研究多智能体协作中的质量、通信成本和状态复用问题。

## 项目解决的问题

项目比较 Text、Protocol、StateVector 和 SharedMemory 在固定公开代码任务上的可观测差异，同时把 private official tests、候选代码、原始响应和凭据留在 Agent 上下文与公开产物之外。

## 系统架构

公开任务经由协议与引用注册表组织；Candidate Parser 处理候选实现；Private Sandbox 在隔离边界运行 official tests；公开记录只保留脱敏计量、状态和聚合结果。Agent 是逻辑职责，不表示每个角色各自调用一次 LLM。

## 两条运行链

1. **确定性 pytest 测试生成 Demo**：PlannerAgent → MemoryAgent → TestGenAgent → ExecutorAgent → SummarizerAgent。TestGenAgent 依据公开任务的确定性 cases 生成 pytest。
2. **M9/M9.1 代码生成实验**：公开 MBPP/HumanEval+ 任务 → Text 或 Protocol 上下文 → 本地 LLM 生成 Python 候选实现 → Candidate Parser → Private Sandbox → official-test 聚合分析。每个任务主要进行一次候选代码生成请求。

两条链共享安全边界和部分基础组件，但实验结论不相互替代。

## 核心模块

- `agents/`：逻辑角色与协作事件。
- `protocol/`：Text、Protocol V1、CompactProtocol V2、能力与引用注册。
- `state/`：StateVector V1/V2。
- `memory/`：SharedMemory V1 与 GatedSharedMemory V2。
- `runtime/`：编排、序列执行与执行端引用解析。
- `experiments/`：M9/M9.1 Spec、Runner 和 Strict Verifier。

## M9/M9.1 结果摘要

| 实验 | 有效 freeze | 主要结果 | 边界 |
| --- | --- | --- | --- |
| M9 | `cc7aac0417afb6acab47baaf7449459692fa9444` | G1/G2/G3/G4 任务成功率为 0.60/0.75/0.75/0.70；G4 相对 G3 为负差异。 | 固定任务、模型与参数。 |
| M9.1 | `c79fd4826627bf61faf5d90540a014d243a59edd` | S1/S2/S3/S4 任务成功率为 0.55/0.55/0.60/0.55；S3 最好，S4 相对 S3 为负差异。 | StateVector 压缩不构成质量因果证明。 |

详细结论见[最终技术报告](reports/最终技术报告.md)、[M9.1 补充实验报告](reports/m9_1/M9.1补充实验报告.md)、[实验结果与统计分析](docs/实验结果与统计分析.md)。离线 Dashboard 由 `scripts/build_competition_dashboard.py` 从公开聚合产物构建。

## 快速运行

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python scripts/audit_competition_delivery.py --root . --allow-incomplete
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
```

## openEuler 部署

部署、依赖与离线同步说明见 [openEuler 部署说明](docs/openEuler部署说明.md)。正式结果只以 openEuler 验收为准；Windows 用于开发与本地验证。

## 实验与报告入口

- [项目总体设计](docs/项目总体设计.md)
- [赛题需求与证据矩阵](docs/赛题需求与证据矩阵.md)
- [实验复现说明](docs/实验复现说明.md)
- [最终技术报告](reports/最终技术报告.md)
- [M9.1 补充实验报告](reports/m9_1/M9.1补充实验报告.md)
- [赛事中文文档与交付物审计报告](reports/赛事中文文档与交付物审计报告.md)

## 安全边界

private tests、candidate code、raw response、canonical solution、private traceback、凭据和个人绝对路径不进入公开文档、Dashboard 或 Agent 上下文。详见[安全沙箱与私有评测](docs/安全沙箱与私有评测.md)。

## 当前限制

Protocol V2 尚未证明降低同口径 Agent 通信 Token 或字符。Memory V2 有真实 query、hit、accept、abstain 和 reuse 记录，但没有质量提升证据。Memory 注入 Token 是 `whitespace_v1` 估算值，不应与 Provider 返回的 prompt token 直接比较。

## 比赛交付物导航

根目录保留演示 PPT、视频和源代码；设计、部署、复现、结果、审计与报告入口均列于本 README。真实签署的参赛承诺书仍须由参赛主体提供，不能用占位文件替代。
