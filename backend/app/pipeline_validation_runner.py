from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationRunResult:
    passed: bool
    commands: list[dict[str, Any]] = field(default_factory=list)


def normalize_validation_commands(raw: object) -> list[list[str]]:
    if not isinstance(raw, list):
        return []
    commands: list[list[str]] = []
    for item in raw:
        if not isinstance(item, list):
            continue
        command = [str(part) for part in item if str(part).strip()]
        if command:
            commands.append(command)
    return commands


def run_validation_commands(
    *,
    workspace: Path,
    commands: list[list[str]],
    timeout_seconds: int = 30,
) -> ValidationRunResult:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                text=True,
                capture_output=True,
                shell=False,
                timeout=timeout_seconds,
                check=False,
            )
            records.append(
                {
                    "command": command,
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "timeout": False,
                }
            )
        except subprocess.TimeoutExpired as exc:
            records.append(
                {
                    "command": command,
                    "exit_code": None,
                    "stdout": exc.stdout or "",
                    "stderr": exc.stderr or "",
                    "timeout": True,
                }
            )
        except OSError as exc:
            records.append(
                {
                    "command": command,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": str(exc),
                    "timeout": False,
                }
            )

    passed = bool(records) and all(record["exit_code"] == 0 and not record["timeout"] for record in records)
    return ValidationRunResult(passed=passed, commands=records)
