from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class PytestResult:
    returncode: int
    stdout: str
    stderr: str
    pytest_missing: bool = False


def run_pytest(run_dir: Path, test_path: Path) -> PytestResult:
    if importlib.util.find_spec("pytest") is None:
        return PytestResult(
            returncode=127,
            stdout="",
            stderr="pytest is not installed; run python -m pip install -r requirements.txt",
            pytest_missing=True,
        )

    relative_test = test_path.relative_to(run_dir)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(relative_test)],
        cwd=run_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    return PytestResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        pytest_missing=False,
    )
