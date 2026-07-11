from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time

from agents.executor import ExecutorAgent
from agents.memory_agent import MemoryAgent
from agents.planner import PlannerAgent
from agents.summarizer import SummarizerAgent
from agents.testgen import TestGenAgent
from evaluation.metrics import build_metrics, write_metrics
from protocol.adapters import get_adapter
from protocol.messages import AgentMessage


class Orchestrator:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def run(self, mode: str, task_path: Path) -> dict:
        if mode not in {"text", "protocol"}:
            raise ValueError("mode must be either 'text' or 'protocol'")

        started = time.perf_counter()
        task = json.loads(task_path.read_text(encoding="utf-8"))
        run_dir = self._make_run_dir(task["task_id"], mode)
        self._materialize_source(task, run_dir)

        adapter = get_adapter(mode)
        messages: list[AgentMessage] = []
        transcript: list[str] = []

        plan_message = PlannerAgent().plan(task)
        self._record(plan_message, messages, transcript, adapter)

        memory_message = MemoryAgent(run_dir / "memory" / "memory.json").remember(task, plan_message)
        self._record(memory_message, messages, transcript, adapter)

        test_path, testgen_message = TestGenAgent().generate(task, run_dir)
        self._record(testgen_message, messages, transcript, adapter)

        pytest_result, executor_message = ExecutorAgent().execute(run_dir=run_dir, test_path=test_path)
        self._record(executor_message, messages, transcript, adapter)

        summary_message = SummarizerAgent().summarize(task, mode, pytest_result, run_dir)
        self._record(summary_message, messages, transcript, adapter)

        duration = time.perf_counter() - started
        metrics = build_metrics(task["task_id"], mode, messages, duration, pytest_result)
        write_metrics(metrics, run_dir / "metrics.json")
        (run_dir / "transcript.txt").write_text("\n".join(transcript), encoding="utf-8")
        return {"run_dir": str(run_dir), "metrics": metrics}

    def _make_run_dir(self, task_id: str, mode: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir = self.project_root / "runs" / task_id / f"{mode}-{stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir

    def _materialize_source(self, task: dict, run_dir: Path) -> None:
        source_path = run_dir / "src" / f"{task['function_name']}.py"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(task["code_under_test"], encoding="utf-8")

    @staticmethod
    def _record(message: AgentMessage, messages: list[AgentMessage], transcript: list[str], adapter) -> None:
        messages.append(message)
        transcript.append(adapter.encode(message))
