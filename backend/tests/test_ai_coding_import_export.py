from __future__ import annotations

import json
from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.pipeline_store import PipelineStore


def _create_definition(store: PipelineStore):
    return store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding Sequential",
            kind="sequential_pipeline",
            stages=[
                {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1},
                {"name": "Review", "role": "reviewer", "agent_id": "agent_reviewer", "stage_order": 2},
                {"name": "Code", "role": "coder", "agent_id": "agent_coder", "stage_order": 3},
                {"name": "Validate", "role": "validator", "agent_id": "agent_validator", "stage_order": 4},
            ],
        )
    )


def _write_legacy_fixture(root: Path) -> Path:
    story_dir = root / "worker" / "stories" / "US-001-dashboard"
    shared_dir = root / "worker" / "shared"
    story_dir.mkdir(parents=True)
    shared_dir.mkdir(parents=True)
    (shared_dir / "prd.md").write_text("# PRD\n\nBuild dashboard product.\n", encoding="utf-8")
    (story_dir / "story.md").write_text("# Story\n\nBuild dashboard cards.\n", encoding="utf-8")
    (story_dir / "status.json").write_text(
        json.dumps({"phase": "coding_complete", "storyId": "US-001-dashboard"}),
        encoding="utf-8",
    )
    (story_dir / "design-v2.md").write_text("# Design\n\nUse cards.\n", encoding="utf-8")
    (story_dir / "implementation.md").write_text("# Implementation\n\nImplemented cards.\n", encoding="utf-8")
    (story_dir / "test-report.md").write_text("# Test Report\n\nPassed.\n", encoding="utf-8")
    return story_dir


def test_import_legacy_story_bundle_creates_pipeline_run(tmp_path: Path) -> None:
    from app.ai_coding_import_export import import_legacy_story_bundle

    story_dir = _write_legacy_fixture(tmp_path)
    store = PipelineStore(tmp_path / "pipeline.db")
    definition = _create_definition(store)

    result = import_legacy_story_bundle(
        store,
        pipeline_id=definition.id,
        story_dir=story_dir,
        shared_prd_path=tmp_path / "worker" / "shared" / "prd.md",
    )
    run = store.get_pipeline_run(result.pipeline_run_id)

    assert run is not None
    assert run.input_payload["story_id"] == "US-001-dashboard"
    assert "Build dashboard cards" in run.input_payload["story"]
    assert {artifact.artifact_type for artifact in run.artifacts} >= {
        "story",
        "prd",
        "design",
        "implementation",
        "validation_report",
    }


def test_export_pipeline_run_writes_legacy_bundle(tmp_path: Path) -> None:
    from app.ai_coding_import_export import export_pipeline_run_to_legacy_bundle

    store = PipelineStore(tmp_path / "pipeline.db")
    definition = _create_definition(store)
    run = store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001-dashboard", input_payload={"story_id": "US-001-dashboard", "story": "# Story\n"}),
    )
    store.create_pipeline_artifact(run.id, artifact_type="prd", name="PRD", content="# PRD\n")
    store.create_pipeline_artifact(run.id, artifact_type="story", name="US-001-dashboard", content="# Story\n")
    store.create_pipeline_artifact(run.id, artifact_type="design", name="design-v2.md", content="# Design\n")
    store.create_pipeline_artifact(run.id, artifact_type="validation_report", name="test-report.md", content="# Tests\n")

    output_dir = export_pipeline_run_to_legacy_bundle(store, run.id, tmp_path / "export")

    assert (output_dir / "stories" / "US-001-dashboard" / "story.md").read_text(encoding="utf-8") == "# Story\n"
    assert (output_dir / "stories" / "US-001-dashboard" / "design-v2.md").read_text(encoding="utf-8") == "# Design\n"
    assert (output_dir / "stories" / "US-001-dashboard" / "test-report.md").read_text(encoding="utf-8") == "# Tests\n"
    assert (output_dir / "shared" / "prd.md").read_text(encoding="utf-8") == "# PRD\n"


def test_export_pipeline_run_is_repeatable(tmp_path: Path) -> None:
    from app.ai_coding_import_export import export_pipeline_run_to_legacy_bundle

    store = PipelineStore(tmp_path / "pipeline.db")
    definition = _create_definition(store)
    run = store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story_id": "US-001", "story": "first"}),
    )
    store.create_pipeline_artifact(run.id, artifact_type="story", name="US-001", content="first")

    first = export_pipeline_run_to_legacy_bundle(store, run.id, tmp_path / "export")
    store.create_pipeline_artifact(run.id, artifact_type="story", name="US-001", content="second")
    second = export_pipeline_run_to_legacy_bundle(store, run.id, tmp_path / "export")

    assert first == second
    assert (second / "stories" / "US-001" / "story.md").read_text(encoding="utf-8") == "second"
