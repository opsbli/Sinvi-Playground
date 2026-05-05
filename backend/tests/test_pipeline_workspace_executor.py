from __future__ import annotations

from pathlib import Path

import pytest


def test_materialize_pipeline_files_writes_declared_relative_files(tmp_path: Path) -> None:
    from app.pipeline_workspace_executor import materialize_pipeline_files

    workspace = tmp_path / "workspace"
    result = materialize_pipeline_files(
        workspace,
        """
Some report.

```pipeline-file path="src/hello.txt"
hello pipeline
```
        """,
    )

    assert result.generated_files == ["src/hello.txt"]
    assert (workspace / "src" / "hello.txt").read_text(encoding="utf-8") == "hello pipeline\n"


def test_materialize_pipeline_files_rejects_paths_outside_workspace(tmp_path: Path) -> None:
    from app.pipeline_workspace_executor import WorkspacePathError, materialize_pipeline_files

    with pytest.raises(WorkspacePathError):
        materialize_pipeline_files(
            tmp_path / "workspace",
            """
```pipeline-file path="../escape.txt"
bad
```
            """,
        )

    assert not (tmp_path / "escape.txt").exists()
