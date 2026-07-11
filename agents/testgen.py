from __future__ import annotations

from pathlib import Path

from protocol.messages import AgentMessage


class TestGenAgent:
    name = "TestGenAgent"

    def generate(self, task: dict, run_dir: Path) -> tuple[Path, AgentMessage]:
        function_name = task["function_name"]
        module_path = Path("src") / f"{function_name}.py"
        module_name = module_path.with_suffix("").as_posix().replace("/", ".")
        test_path = run_dir / "tests" / f"test_{module_path.stem}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)

        cases = task.get("cases", [])
        case_lines = [f"    ({repr(c['input'])}, {repr(c['expected'])})," for c in cases]
        rendered_cases = "\n".join(case_lines) or "    ({}, None),"
        code = f'''from {module_name} import {function_name}


def test_{function_name}_examples():
    cases = [
{rendered_cases}
    ]
    for kwargs, expected in cases:
        assert {function_name}(**kwargs) == expected
'''
        test_path.write_text(code, encoding="utf-8")
        message = AgentMessage(
            sender=self.name,
            receiver="ExecutorAgent",
            role="test_generation",
            content=f"Generated pytest file at {test_path.as_posix()}.",
            metadata={"test_path": str(test_path), "case_count": len(cases)},
        )
        return test_path, message
