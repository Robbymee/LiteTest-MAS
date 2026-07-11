from __future__ import annotations

import json
from pathlib import Path

from protocol.messages import AgentMessage
from sandbox.local_pytest import PytestResult


def estimate_token_count(text: str) -> int:
    return len(text.split())


def build_metrics(
    task_id: str,
    mode: str,
    messages: list[AgentMessage],
    duration_sec: float,
    pytest_result: PytestResult,
) -> dict:
    serialized = [message.to_json() for message in messages]
    return {
        "task_id": task_id,
        "mode": mode,
        "success": pytest_result.returncode == 0,
        "agent_message_count": len(messages),
        "char_count_total": sum(len(item) for item in serialized),
        "token_count_total": sum(estimate_token_count(item) for item in serialized),
        "total_duration_sec": round(duration_sec, 6),
        "pytest_returncode": pytest_result.returncode,
    }


def write_metrics(metrics: dict, path: Path) -> None:
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
