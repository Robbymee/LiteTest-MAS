from __future__ import annotations

import json
from pathlib import Path

from protocol.messages import AgentMessage
from sandbox.local_pytest import PytestResult


class SummarizerAgent:
    name = "SummarizerAgent"

    def summarize(self, task: dict, mode: str, result: PytestResult, run_dir: Path) -> AgentMessage:
        success = result.returncode == 0
        summary = {
            "task_id": task["task_id"],
            "mode": mode,
            "success": success,
            "pytest_returncode": result.returncode,
            "pytest_missing": result.pytest_missing,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        summary_path = run_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return AgentMessage(
            sender=self.name,
            receiver="Orchestrator",
            role="summary",
            content=f"Task {task['task_id']} success={success}; summary written to {summary_path.as_posix()}.",
            metadata={"summary_path": str(summary_path), "success": success},
        )
