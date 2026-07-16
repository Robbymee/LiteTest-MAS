# 安全与数据边界

公开层只允许脱敏任务身份、聚合指标、记录状态和校验信息。禁止公开或传递 `hidden_reference_tests`、candidate code、raw response、canonical solution、private traceback、凭据、请求 ID、用户目录和模型绝对路径。

Private Sandbox 在 Agent 生成之后执行 official tests，公开 Runner 只记录安全计数和分类。Protocol、StateVector、SharedMemory 与 Dashboard 都必须拒绝私有字段。安全扫描发现问题时必须保留审计结果并修复边界，不能删除失败记录。
