from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .pipeline_schemas import PipelineArtifact, PipelineRunCreate
from .pipeline_store import PipelineStore


LEGACY_ARTIFACT_FILES = {
    "design-v1.md": "design",
    "design-v2.md": "design",
    "design-review-report.md": "design_review",
    "implementation.md": "implementation",
    "test-report.md": "validation_report",
}

EXPORT_FILE_BY_ARTIFACT_TYPE = {
    "design": "design-v2.md",
    "design_review": "design-review-report.md",
    "implementation": "implementation.md",
    "validation_report": "test-report.md",
}


@dataclass(frozen=True)
class LegacyStoryImportResult:
    pipeline_run_id: str
    story_id: str


def parse_prd(prd_path: Path | None) -> str | None:
    if prd_path is None or not prd_path.exists():
        return None
    return prd_path.read_text(encoding="utf-8")


def parse_worker_story(story_dir: Path) -> dict[str, Any]:
    story_path = story_dir / "story.md"
    status_path = story_dir / "status.json"
    if not story_path.exists():
        raise FileNotFoundError(f"Legacy story file is missing: {story_path}")

    status: dict[str, Any] = {}
    if status_path.exists():
        raw_status = json.loads(status_path.read_text(encoding="utf-8"))
        if isinstance(raw_status, dict):
            status = raw_status

    story_id = str(status.get("storyId") or story_dir.name).strip() or story_dir.name
    return {
        "story_id": story_id,
        "story": story_path.read_text(encoding="utf-8"),
        "status": status,
    }


def _import_legacy_artifacts(store: PipelineStore, run_id: str, story_dir: Path) -> None:
    for file_name, artifact_type in LEGACY_ARTIFACT_FILES.items():
        path = story_dir / file_name
        if not path.exists():
            continue
        store.create_pipeline_artifact(
            run_id,
            artifact_type=artifact_type,
            name=file_name,
            content=path.read_text(encoding="utf-8"),
            metadata={"source_path": str(path)},
        )


def import_legacy_story_bundle(
    store: PipelineStore,
    *,
    pipeline_id: str,
    story_dir: Path,
    shared_prd_path: Path | None = None,
) -> LegacyStoryImportResult:
    parsed = parse_worker_story(story_dir)
    run = store.create_pipeline_run(
        pipeline_id,
        PipelineRunCreate(
            title=parsed["story_id"],
            input_payload={
                "story_id": parsed["story_id"],
                "story": parsed["story"],
                "legacy_status": parsed["status"],
                "source_story_dir": str(story_dir),
            },
        ),
    )
    store.create_pipeline_artifact(
        run.id,
        artifact_type="story",
        name=parsed["story_id"],
        content=parsed["story"],
        metadata={"story_id": parsed["story_id"], "source_path": str(story_dir / "story.md")},
    )
    prd_content = parse_prd(shared_prd_path)
    if prd_content is not None:
        store.create_pipeline_artifact(
            run.id,
            artifact_type="prd",
            name="PRD",
            content=prd_content,
            metadata={"source_path": str(shared_prd_path)},
        )
    _import_legacy_artifacts(store, run.id, story_dir)
    return LegacyStoryImportResult(pipeline_run_id=run.id, story_id=parsed["story_id"])


def _latest_artifact(artifacts: list[PipelineArtifact], artifact_type: str) -> PipelineArtifact | None:
    matches = [artifact for artifact in artifacts if artifact.artifact_type == artifact_type]
    return matches[-1] if matches else None


def _story_id_from_run(run) -> str:  # noqa: ANN001
    raw = str(run.input_payload.get("story_id") or run.title or run.id).strip()
    return raw.replace("\\", "-").replace("/", "-") or run.id


def export_pipeline_run_to_legacy_bundle(store: PipelineStore, run_id: str, output_dir: Path) -> Path:
    run = store.get_pipeline_run(run_id)
    if run is None:
        raise ValueError("Pipeline run not found.")

    story_id = _story_id_from_run(run)
    story_dir = output_dir / "stories" / story_id
    shared_dir = output_dir / "shared"
    story_dir.mkdir(parents=True, exist_ok=True)
    shared_dir.mkdir(parents=True, exist_ok=True)

    story_artifact = _latest_artifact(run.artifacts, "story")
    story_content = story_artifact.content if story_artifact else str(run.input_payload.get("story") or "")
    (story_dir / "story.md").write_text(story_content, encoding="utf-8")

    status = {
        "storyId": story_id,
        "phase": run.status,
        "pipelineRunId": run.id,
    }
    (story_dir / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    prd_artifact = _latest_artifact(run.artifacts, "prd")
    if prd_artifact is not None:
        (shared_dir / "prd.md").write_text(prd_artifact.content, encoding="utf-8")

    for artifact_type, file_name in EXPORT_FILE_BY_ARTIFACT_TYPE.items():
        artifact = _latest_artifact(run.artifacts, artifact_type)
        if artifact is not None:
            (story_dir / file_name).write_text(artifact.content, encoding="utf-8")

    return output_dir
