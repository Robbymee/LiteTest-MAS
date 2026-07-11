from __future__ import annotations

from pathlib import Path

from protocol.messages import AgentMessage
from sandbox.local_pytest import PytestResult, run_pytest


class ExecutorAgent:
    name = "ExecutorAgent"

    def execute(self, run_dir: Path, test_path: Path) -> tuple[PytestResult, AgentMessage]:
        result = run_pytest(run_dir=run_dir, test_path=test_path)
        content = f"Pytest finished with return code {result.returncode}."
        if result.pytest_missing:
            content = "Pytest is not installed. Run python -m pip install -r requirements.txt."
        return result, AgentMessage(
            sender=self.name,
            receiver="SummarizerAgent",
            role="execution",
            content=content,
            metadata={"returncode": result.returncode, "pytest_missing": result.pytest_missing},
        )
