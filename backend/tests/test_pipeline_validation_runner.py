from __future__ import annotations

from pathlib import Path

import sys


def test_run_validation_commands_records_success(tmp_path: Path) -> None:
    from app.pipeline_validation_runner import run_validation_commands

    result = run_validation_commands(
        workspace=tmp_path,
        commands=[[sys.executable, "-c", "print('ok')"]],
        timeout_seconds=5,
    )

    assert result.passed is True
    assert result.commands[0]["exit_code"] == 0
    assert result.commands[0]["stdout"].strip() == "ok"


def test_run_validation_commands_records_failure(tmp_path: Path) -> None:
    from app.pipeline_validation_runner import run_validation_commands

    result = run_validation_commands(
        workspace=tmp_path,
        commands=[[sys.executable, "-c", "import sys; print('bad'); sys.exit(3)"]],
        timeout_seconds=5,
    )

    assert result.passed is False
    assert result.commands[0]["exit_code"] == 3
    assert result.commands[0]["stdout"].strip() == "bad"
