import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_run_10_rounds_group_a_text_mode():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_10_rounds.py",
            "--group",
            "A",
            "--modes",
            "text",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert Path(payload["summary_path"]).exists()
    assert payload["summary"]["task_count"] == 5
    assert payload["summary"]["run_count"] == 5
    assert payload["summary"]["aggregates_by_mode"]["text"]["success_rate"] == 1.0
