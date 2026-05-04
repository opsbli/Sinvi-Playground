from __future__ import annotations

import sqlite3
from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.store_schema import initialize_schema


def test_initialize_schema_creates_pipeline_tables() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)

    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'pipeline_%'"
    ).fetchall()
    names = {row["name"] for row in rows}

    assert "pipeline_definitions" in names
    assert "pipeline_stage_definitions" in names
    assert "pipeline_runs" in names
    assert "pipeline_stage_runs" in names
    assert "pipeline_artifacts" in names


def test_pipeline_store_creates_definition_and_run(tmp_path: Path) -> None:
    from app.pipeline_store import PipelineStore

    store = PipelineStore(tmp_path / "pipeline.db")
    definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding",
            kind="sequential_pipeline",
            description="Story execution pipeline.",
            stages=[
                {
                    "name": "Design",
                    "role": "designer",
                    "agent_id": "agent_designer",
                    "stage_order": 1,
                },
                {
                    "name": "Review",
                    "role": "reviewer",
                    "agent_id": "agent_reviewer",
                    "stage_order": 2,
                },
            ],
        )
    )

    run = store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story": "Build layout"}),
    )
    detail = store.get_pipeline_run(run.id)

    assert detail is not None
    assert detail.current_stage_id == definition.stages[0].id
    assert [stage.status for stage in detail.stage_runs] == ["pending", "pending"]
