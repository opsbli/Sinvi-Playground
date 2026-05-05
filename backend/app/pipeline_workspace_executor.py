from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .pipeline_store import PipelineStore


PIPELINE_FILE_BLOCK_RE = re.compile(
    r"```pipeline-file\s+path=\"(?P<path>[^\"]+)\"\s*\n(?P<content>.*?)\n?```",
    re.DOTALL,
)


class WorkspacePathError(ValueError):
    pass


@dataclass(frozen=True)
class WorkspaceMaterializationResult:
    workspace: Path
    generated_files: list[str] = field(default_factory=list)


def workspace_root_for_run(store: PipelineStore, pipeline_run_id: str) -> Path:
    return (store.db_path.parent / "pipeline-workspaces" / pipeline_run_id).resolve()


def _resolve_workspace_file(workspace: Path, raw_path: str) -> Path:
    normalized = str(raw_path or "").strip().replace("\\", "/")
    if not normalized:
        raise WorkspacePathError("Pipeline file path is empty.")
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise WorkspacePathError(f"Absolute pipeline file paths are not allowed: {raw_path}")
    resolved_workspace = workspace.resolve()
    resolved = (resolved_workspace / candidate).resolve()
    try:
        resolved.relative_to(resolved_workspace)
    except ValueError as exc:
        raise WorkspacePathError(f"Pipeline file path escapes workspace: {raw_path}") from exc
    return resolved


def materialize_pipeline_files(workspace: Path, content: str) -> WorkspaceMaterializationResult:
    workspace = workspace.resolve()
    generated: list[str] = []
    for match in PIPELINE_FILE_BLOCK_RE.finditer(content or ""):
        target = _resolve_workspace_file(workspace, match.group("path"))
        target.parent.mkdir(parents=True, exist_ok=True)
        file_content = match.group("content")
        target.write_text(file_content if file_content.endswith("\n") else f"{file_content}\n", encoding="utf-8")
        generated.append(target.relative_to(workspace).as_posix())
    return WorkspaceMaterializationResult(workspace=workspace, generated_files=generated)
