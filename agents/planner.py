from __future__ import annotations

from protocol.messages import AgentMessage


class PlannerAgent:
    name = "PlannerAgent"

    def plan(self, task: dict) -> AgentMessage:
        function_name = task["function_name"]
        source_path = f"src/{function_name}.py"
        cases = task.get("cases", [])
        content = (
            f"Create pytest tests for {function_name} in {source_path}. "
            f"Use {len(cases)} deterministic example cases from the task spec."
        )
        return AgentMessage(
            sender=self.name,
            receiver="TestGenAgent",
            role="plan",
            content=content,
            metadata={"task_id": task["task_id"], "case_count": len(cases)},
        )
