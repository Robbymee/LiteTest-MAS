# M9.1 赛题对齐强化实验

本目录保存独立 M9.1 Spec。实验组为 S1 Text baseline、S2 CompactProtocol V2、S3 CompactProtocol V2 + StateVector V2、S4 CompactProtocol V2 + StateVector V2 + GatedSharedMemory V2。

M9.1 使用与 M9 相同的公开任务、模型、seed、生成参数、Parser、Sandbox 和 official-test 评测边界，但拥有独立 `result_scope` 和 `conclusion_scope`。正式运行前必须完成单元测试、双平台全量测试、fake canary、两项真实 canary、public leakage 检查、implementation freeze 和 freeze SHA 运行校验。

本阶段只生成 Spec 和运行前门槛，不复制 M9 结果，不读取 private tests 调参，也不启动正式 240 条运行。
