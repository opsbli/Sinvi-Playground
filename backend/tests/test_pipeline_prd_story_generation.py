from __future__ import annotations

import sqlite3
from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.pipeline_store import PipelineStore
from app.store import SQLitePlaygroundStore


def test_prd_and_story_artifact_schemas_accept_required_fields() -> None:
    from app.pipeline_prd_story import PrdArtifactCreate, StoryArtifactCreate

    prd = PrdArtifactCreate(brief="Build a dashboard for project health.")
    story = StoryArtifactCreate(
        story_id="US-001",
        title="Project health dashboard",
        content="As a user, I can view project health.",
        source_prd_artifact_id="partifact_prd",
    )

    assert prd.artifact_type == "prd"
    assert story.artifact_type == "story"


def test_pipeline_store_creates_pipeline_artifact(tmp_path: Path) -> None:
    store = PipelineStore(tmp_path / "pipeline.db")
    definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="PRD Story Generation",
            kind="prd_story_generation",
            stages=[
                {"name": "PRD Writer", "role": "prd_writer", "agent_id": "agent_prd", "stage_order": 1}
            ],
        )
    )
    run = store.create_pipeline_run(definition.id, PipelineRunCreate(title="Brief", input_payload={"brief": "x"}))

    artifact = store.create_pipeline_artifact(
        run.id,
        artifact_type="prd",
        name="PRD",
        content="# PRD\n",
        metadata={"brief": "x"},
    )
    detail = store.get_pipeline_run(run.id)

    assert artifact.artifact_type == "prd"
    assert detail is not None
    assert detail.artifacts[0].id == artifact.id
    assert detail.artifacts[0].metadata["brief"] == "x"


def test_seed_prd_story_agents_is_idempotent(tmp_path: Path) -> None:
    from app.seeds.pipeline_prd_story_agents import seed_prd_story_agents

    store = SQLitePlaygroundStore(tmp_path / "playground.db")

    first = seed_prd_story_agents(store)
    second = seed_prd_story_agents(store)

    assert first.imported == 2
    assert second.imported == 0
    assert second.updated == 2
    assert second.agent_ids_by_role == first.agent_ids_by_role

    with store._connect() as connection:
        rows = connection.execute(
            """
            SELECT pipeline_family, role
            FROM agent_import_metadata
            WHERE pipeline_family = 'ai_coding' AND role IN ('prd_writer', 'story_splitter')
            ORDER BY role ASC
            """
        ).fetchall()

    assert [row["role"] for row in rows] == ["prd_writer", "story_splitter"]


def test_prd_story_generation_creates_prd_and_story_artifacts(tmp_path: Path) -> None:
    from app.pipeline_prd_story import run_prd_story_generation

    store = PipelineStore(tmp_path / "pipeline.db")
    definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="PRD Story Generation",
            kind="prd_story_generation",
            stages=[
                {"name": "PRD Writer", "role": "prd_writer", "agent_id": "agent_prd", "stage_order": 1},
                {
                    "name": "Story Splitter",
                    "role": "story_splitter",
                    "agent_id": "agent_story",
                    "stage_order": 2,
                },
            ],
        )
    )

    result = run_prd_story_generation(
        store,
        definition.id,
        brief="Build a project health dashboard with status cards and risk alerts.",
    )
    run = store.get_pipeline_run(result.pipeline_run_id)

    assert run is not None
    assert result.prd_artifact.artifact_type == "prd"
    assert result.story_artifacts
    assert {artifact.artifact_type for artifact in run.artifacts} == {"prd", "story"}
    assert result.story_artifacts[0].metadata["source_prd_artifact_id"] == result.prd_artifact.id


def test_story_splitter_ignores_non_story_prd_bullets() -> None:
    from app.pipeline_prd_story import split_prd_into_stories

    stories = split_prd_into_stories(
        """
# PRD

## Goals
- Deliver a dashboard

## User Stories Seed
- Build status cards
- Build risk alerts

## Non-Goals
- Do not execute implementation agents
        """,
        source_prd_artifact_id="partifact_prd",
    )

    assert [story.title for story in stories] == ["status cards", "risk alerts"]


def test_story_artifact_can_seed_sequential_pipeline_run(tmp_path: Path) -> None:
    from app.pipeline_prd_story import run_prd_story_generation

    store = PipelineStore(tmp_path / "pipeline.db")
    generation_definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="PRD Story Generation",
            kind="prd_story_generation",
            stages=[
                {"name": "PRD Writer", "role": "prd_writer", "agent_id": "agent_prd", "stage_order": 1},
                {"name": "Story Splitter", "role": "story_splitter", "agent_id": "agent_story", "stage_order": 2},
            ],
        )
    )
    execution_definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding Sequential",
            kind="sequential_pipeline",
            stages=[
                {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1}
            ],
        )
    )
    result = run_prd_story_generation(store, generation_definition.id, brief="Build a dashboard.")
    story = result.story_artifacts[0]

    run = store.create_pipeline_run(
        execution_definition.id,
        PipelineRunCreate(
            title=story.metadata["story_id"],
            input_payload={"story_artifact_id": story.id, "story": story.content},
        ),
    )

    assert run.input_payload["story_artifact_id"] == story.id
    assert "Build a dashboard" in run.input_payload["story"]
