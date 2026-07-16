# LiteTest-MAS 多智能体测试生成系统

## 项目简介

LiteTest-MAS 是面向测试生成的低开销多智能体系统。它在固定公开任务上比较 Text、Protocol、StateVector 和 SharedMemory，并将 private official tests 保持在 Agent 上下文之外。

## 系统组成

- `agents/`：Planner、Memory、TestGen、Executor、Summarizer 等逻辑角色。
- `protocol/`：Text、Protocol V1 与独立 CompactProtocol V2。
- `state/`：StateVector V1 与独立 StateVector V2。
- `memory/`：SharedMemory V1 与 GatedSharedMemory V2。
- `sandbox/`、`evaluator/`：Candidate Parser、Private Sandbox 与 Strict Verifier 边界。
- `experiments/`：M9 与 M9.1 Spec、Runner 和校验器。
- `reports/`：仅含公开聚合、统计和脱敏报告。

## 正式实验

M9 的有效 freeze 为 `cc7aac0417afb6acab47baaf7449459692fa9444`，完成 240/240 final records。其 G1/G2/G3/G4 任务成功率为 0.60、0.75、0.75、0.70。M9 说明 Protocol V1 在本次固定条件下提高任务成功率，但总 Token 和延迟更高；StateVector V1 无成功率增益；SharedMemory V1 有真实复用且存在负迁移风险。

M9.1 的有效 freeze 为 `c79fd4826627bf61faf5d90540a014d243a59edd`，完成独立 240/240 final records。S1/S2/S3/S4 的任务成功率为 0.55、0.55、0.60、0.55。其结论仅适用于固定任务、固定模型和固定参数，详见 `reports/M9.1补充实验报告.md` 与 `reports/最终技术报告.md`。

## 快速验证

在仓库根目录运行：

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python scripts/audit_competition_delivery.py --root . --allow-incomplete
```

Windows 需设置：

```powershell
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
```

POSIX 环境需设置：

```bash
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
```

## 文档入口

- 系统设计：`docs/项目总体设计.md`
- 赛题证据：`docs/赛题需求与证据矩阵.md`
- 部署与复现：`docs/Windows部署说明.md`、`docs/openEuler部署说明.md`、`docs/实验复现说明.md`
- 安全边界：`docs/安全沙箱与私有评测.md`
- 离线 Dashboard：`docs/演示操作指南.md`
- 交付审计：`reports/赛事中文文档与交付物审计报告.md`

## 安全与发布

private tests、candidate code、raw response、canonical solution、凭据、用户目录和模型绝对路径不进入公开文档、Dashboard 或 Agent 上下文。保留 `v1.0.0-experiment`；在严格交付审计通过及真实赛事材料齐备前，不创建 `v1.1.0-competition`。
