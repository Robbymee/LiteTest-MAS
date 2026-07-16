# openEuler 部署说明

## 前置条件

目标平台为 openEuler 24.03-LTS-SP3 x86_64，使用 Python 3.11 或兼容版本。仓库路径可自选，以下命令均从仓库根目录运行：

```bash
python3 -m pip install -r requirements.txt
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python3 -m pytest tests -q
```

## 同步与验收

当远端 DNS 不可用时，可使用由 Windows 已验证提交生成的 Git bundle，并在 openEuler 执行 `git fetch <bundle> main` 与 `git merge --ff-only FETCH_HEAD`。不得修改 DNS、网络、Git 历史、冻结 worktree 或发布标签以绕过验收。

```bash
python3 scripts/audit_competition_delivery.py --root . --allow-incomplete
python3 scripts/build_competition_dashboard.py --m9-dir reports/m9 --m9-1-dir reports/m9_1 --output-dir /tmp/dashboard-output
git diff --check
```

只有在相同 SHA 的 Windows 与 openEuler 测试均通过后，才记录双平台验收。正式实验只可在预注册 freeze worktree 上执行。
