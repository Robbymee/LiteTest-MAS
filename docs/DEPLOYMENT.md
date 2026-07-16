# 部署说明

Windows 部署见 `docs/Windows部署说明.md`，openEuler 部署见 `docs/openEuler部署说明.md`。基础依赖为 `requirements.txt`；真实模型服务与仓库运行环境解耦，未启动服务时可运行测试、聚合、审计和离线 Dashboard。

正式 M9/M9.1 只可在相应 freeze 的 openEuler worktree 执行。部署过程不得暴露凭据、用户目录、模型绝对路径或私有评测数据。
