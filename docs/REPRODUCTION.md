# 复现说明

完整中文说明见 `docs/实验复现说明.md`。从仓库根目录设置 `PYTHONPATH` 后运行：

```bash
python -m pytest tests -q
python scripts/audit_competition_delivery.py --root . --allow-incomplete
```

M9/M9.1 的公开聚合可复现，private tests 与模型原始响应不可公开重放。正式结果必须在 openEuler 的相应 freeze worktree 验收。
