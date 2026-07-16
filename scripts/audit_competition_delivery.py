from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REQUIRED_DOCUMENTS = (
    "README.md",
    "docs/项目总体设计.md",
    "docs/赛题需求与证据矩阵.md",
    "docs/多智能体角色与协作流程.md",
    "docs/结构化通信协议设计.md",
    "docs/非文本状态传递设计.md",
    "docs/共享记忆设计与门控策略.md",
    "docs/关联连续任务设计说明.md",
    "docs/安全沙箱与私有评测.md",
    "docs/Windows部署说明.md",
    "docs/openEuler部署说明.md",
    "docs/实验复现说明.md",
    "docs/实验结果与统计分析.md",
    "docs/演示操作指南.md",
    "docs/常见故障排查.md",
    "docs/匿名化与赛事提交检查.md",
    "reports/m9/赛题指标补充分析.md",
    "reports/m9/随机种子相关性分析.md",
    "reports/m9_1/M9.1补充实验报告.md",
    "reports/最终技术报告.md",
)
PROTECTED_REVISIONS = {
    "m9_freeze": "cc7aac0417afb6acab47baaf7449459692fa9444",
    "m9_1_freeze": "c79fd4826627bf61faf5d90540a014d243a59edd",
    "release_tag": "v1.0.0-experiment",
}
PATH_PATTERN = re.compile(r"(?:[A-Za-z]:\\(?:Users|Documents and Settings)\\|/(?:home|Users|root)/)", re.I)
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|authorization|access[_-]?token|secret)\s*[:=]\s*[^\s`'\"]{4,}"
)
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_PATTERN = re.compile(r"^\s*```", re.M)
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """在仓库根目录执行只读 Git 命令并返回结果。"""
    return subprocess.run(
        ["git", *args], cwd=root, text=True, encoding="utf-8", errors="strict", capture_output=True
    )


def tracked_markdown(root: Path) -> list[Path]:
    """返回 Git 已跟踪或已暂存的项目 Markdown 路径。"""
    result = _git(root, "ls-files", "-z", "--", "*.md")
    if result.returncode != 0:
        raise RuntimeError("git_ls_files_failed:" + result.stderr.strip())
    return [root / item for item in result.stdout.split("\0") if item]


def _without_fenced_code(text: str) -> str:
    """移除围栏代码块，避免把命令和标识符计入正文语言判断。"""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            lines.append(line)
    return "\n".join(lines)


def _local_link_errors(path: Path, root: Path, text: str) -> list[str]:
    """检查 Markdown 中不含锚点的本地相对链接是否存在。"""
    errors: list[str] = []
    for raw_target in LINK_PATTERN.findall(_without_fenced_code(text)):
        target = raw_target.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = target.split(maxsplit=1)[0]
        target = target.split("#", 1)[0]
        if not target or re.match(r"^(?:https?://|mailto:|data:)", target, re.I):
            continue
        candidate = (path.parent / target).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append(f"link_outside_repository:{target}")
            continue
        if not candidate.exists():
            errors.append(f"missing_link:{target}")
    return errors


def audit_markdown(path: Path, root: Path) -> dict[str, Any]:
    """审计一份 Markdown 的编码、中文正文、围栏、链接和敏感值。"""
    relative = path.relative_to(root).as_posix()
    errors: list[str] = []
    try:
        text = path.read_bytes().decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"path": relative, "valid": False, "chinese_characters": 0, "errors": ["invalid_utf8"]}
    body = _without_fenced_code(text)
    chinese_count = len(CHINESE_PATTERN.findall(body))
    if chinese_count == 0:
        errors.append("chinese_body_missing")
    if len(FENCE_PATTERN.findall(text)) % 2:
        errors.append("unbalanced_code_fence")
    errors.extend(_local_link_errors(path, root, text))
    if PATH_PATTERN.search(text):
        errors.append("personal_absolute_path")
    if SECRET_PATTERN.search(text):
        errors.append("credential_value")
    return {"path": relative, "valid": not errors, "chinese_characters": chinese_count, "errors": errors}


def _delivery_inventory(root: Path) -> dict[str, bool]:
    """检查赛事根目录和中文文档体系的必需交付类别。"""
    root_files = [path for path in root.iterdir() if path.is_file()]
    return {
        "readme": (root / "README.md").is_file(),
        "chinese_design_documents": all((root / path).is_file() for path in REQUIRED_DOCUMENTS[1:16]),
        "technical_report": (root / "reports/最终技术报告.md").is_file(),
        "commitment_letter": any("承诺" in path.name for path in root_files),
        "presentation": any(path.suffix.lower() in {".ppt", ".pptx"} for path in root_files),
        "video_or_download_instructions": any(
            path.suffix.lower() in {".mp4", ".webm", ".mov"} or "视频" in path.name for path in root_files
        ),
        "complete_source": all((root / name).is_dir() for name in ("agents", "runtime", "protocol", "state", "memory")),
        "deployment_and_reproduction": all(
            (root / name).is_file()
            for name in ("docs/Windows部署说明.md", "docs/openEuler部署说明.md", "docs/实验复现说明.md")
        ),
    }


def _protected_revisions(root: Path) -> dict[str, dict[str, Any]]:
    """验证冻结提交和既有发布标签仍可解析。"""
    results: dict[str, dict[str, Any]] = {}
    for name, revision in PROTECTED_REVISIONS.items():
        result = _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
        results[name] = {
            "revision": revision,
            "valid": result.returncode == 0,
            "resolved_sha": result.stdout.strip() if result.returncode == 0 else "unavailable",
        }
    return results


def audit_repository(root: Path, markdown_paths: Iterable[Path] | None = None) -> dict[str, Any]:
    """审计仓库中文 Markdown、赛事交付清单和受保护版本。"""
    root = root.resolve()
    paths = list(markdown_paths) if markdown_paths is not None else tracked_markdown(root)
    markdown = [audit_markdown(path.resolve(), root) for path in paths]
    missing_documents = [path for path in REQUIRED_DOCUMENTS if not (root / path).is_file()]
    delivery = _delivery_inventory(root)
    revisions = _protected_revisions(root)
    summary = {
        "tracked_markdown_count": len(markdown),
        "markdown_pass_count": sum(item["valid"] for item in markdown),
        "markdown_failure_count": sum(not item["valid"] for item in markdown),
        "required_document_count": len(REQUIRED_DOCUMENTS),
        "missing_document_count": len(missing_documents),
        "delivery_pass_count": sum(delivery.values()),
        "delivery_requirement_count": len(delivery),
    }
    valid = (
        summary["markdown_failure_count"] == 0
        and not missing_documents
        and all(delivery.values())
        and all(item["valid"] for item in revisions.values())
    )
    return {
        "schema_version": "1.0",
        "valid": valid,
        "summary": summary,
        "missing_documents": missing_documents,
        "delivery": delivery,
        "protected_revisions": revisions,
        "markdown": markdown,
    }


def write_report(result: dict[str, Any], path: Path) -> None:
    """将审计结果写为不掩盖缺口的中文 Markdown 报告。"""
    summary = result["summary"]
    failed = [item for item in result["markdown"] if not item["valid"]]
    lines = [
        "# 赛事中文文档与交付物审计报告",
        "",
        "## 审计结论",
        "",
        f"当前审计结果为 `valid={str(result['valid']).lower()}`。该值反映交付完整性，不代表审计工具是否正常运行。",
        f"共审计 {summary['tracked_markdown_count']} 份 tracked Markdown，其中 {summary['markdown_pass_count']} 份通过、{summary['markdown_failure_count']} 份存在缺口；指定中文文档缺失 {summary['missing_document_count']} 份。",
        "",
        "## Markdown 缺口",
        "",
        "| 路径 | 问题 |",
        "| --- | --- |",
    ]
    lines.extend(f"| `{item['path']}` | {', '.join(item['errors'])} |" for item in failed)
    lines.extend(["", "## 缺失中文文档", ""])
    if result["missing_documents"]:
        lines.extend(f"- `{item}`" for item in result["missing_documents"])
    else:
        lines.append("- 无")
    lines.extend(["", "## 根目录交付清单", "", "| 类别 | 状态 |", "| --- | --- |"]) 
    lines.extend(f"| `{name}` | {'已存在' if value else '缺失'} |" for name, value in result["delivery"].items())
    lines.extend(["", "## 受保护版本", "", "| 名称 | 修订 | 状态 |", "| --- | --- | --- |"]) 
    lines.extend(
        f"| `{name}` | `{item['revision']}` | {'可解析' if item['valid'] else '缺失'} |"
        for name, item in result["protected_revisions"].items()
    )
    lines.extend(
        [
            "",
            "## 边界说明",
            "",
            "本阶段只建立并执行审计，不改写 M9/M9.1 正式结果，不创建承诺书、PPT 或视频占位文件，也不修改冻结提交和既有发布标签。英文主体文档和缺失交付物必须在后续独立阶段逐项修复并重新审计。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("\n".join(lines).encode("utf-8"))


def main() -> int:
    """执行赛事中文 Markdown 与最终交付物审计命令。"""
    parser = argparse.ArgumentParser(description="审计中文 Markdown 与赛事最终交付物")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    try:
        result = audit_repository(root)
        if args.report:
            write_report(result, Path(args.report))
    except (OSError, RuntimeError) as error:
        print(f"赛事交付审计失败：{error}", file=sys.stderr)
        return 2
    # CLI 使用 ASCII 转义，避免 Windows 默认 GBK 控制台无法输出异常文件名字符。
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["valid"] or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
