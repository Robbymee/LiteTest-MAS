# M9 正式结果

M9 的有效 freeze 为 `cc7aac0417afb6acab47baaf7449459692fa9444`，Strict Verifier 验证 240/240 final records、零缺失、零重复和零公开泄漏。任务成功数为 168，72 条 official-test 失败作为模型质量结果保留，基础设施失败为零。

G1/G2/G3/G4 任务成功率为 0.60、0.75、0.75、0.70。G2-G1 的配对差为 +0.15，95% CI 为 [+0.0333, +0.2671]；G3-G2 为 0.00；G4-G3 为 -0.05。Protocol V1 提高本次任务成功率但增加总 Token 和延迟；StateVector V1 未提高成功率；SharedMemory V1 发生真实复用但存在负迁移风险。

详细公开指标见 `reports/m9/赛题指标补充分析.md` 与 `reports/m9/随机种子相关性分析.md`。
