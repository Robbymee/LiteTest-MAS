# Windows 部署说明

## 前置条件

使用 Python 3.11 或兼容版本、Git 与 PowerShell。在仓库根目录安装基础依赖：

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
```

真实模型服务是独立的本地服务；文档不记录其绝对路径、凭据或用户目录。未启动模型服务时，只运行 Mock、聚合、Dashboard 与文档审计命令。

## 验证

```powershell
python -m pytest tests -q
python scripts/audit_competition_delivery.py --root . --allow-incomplete
python scripts/build_competition_dashboard.py --m9-dir reports/m9 --m9-1-dir reports/m9_1 --output-dir .\dashboard-output
```

`dashboard-output` 只包含 `data.json` 与离线 `index.html`。正式 M9/M9.1 不在 Windows 重新运行，正式结果以 openEuler freeze 运行和公开聚合为准。
