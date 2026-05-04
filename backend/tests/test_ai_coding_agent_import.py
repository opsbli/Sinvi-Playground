from __future__ import annotations

import sqlite3
from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate
from app.pipeline_store import PipelineStore
from app.store import SQLitePlaygroundStore
from app.store_schema import initialize_schema


AI_CODING_ROLES = ("designer", "reviewer", "coder", "validator")


def _write_agent_prompts(agents_dir: Path) -> None:
    agents_dir.mkdir(parents=True)
    for role in AI_CODING_ROLES:
        (agents_dir / f"{role}.md").write_text(
            f"# {role.title()} Agent\n\nYou are the ai_coding {role} agent.\n",
            encoding="utf-8",
        )


def _metadata_rows(store: SQLitePlaygroundStore) -> list[sqlite3.Row]:
    with store._connect() as connection:
        return connection.execute(
            """
            SELECT agent_id, pipeline_family, role, source_provider, source_path, source_hash
            FROM agent_import_metadata
            ORDER BY role ASC
            """
        ).fetchall()


def test_initialize_schema_creates_agent_import_metadata_table() -> None:
    connection = sqlite3.connect(":memory:")
    initialize_schema(connection)

    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'agent_import_metadata'
        """
    ).fetchone()

    assert row is not None


def test_import_ai_coding_agents_creates_four_role_agents(tmp_path: Path) -> None:
    from app.seeds.ai_coding_agents import import_ai_coding_agents

    agents_dir = tmp_path / "agents"
    _write_agent_prompts(agents_dir)
    store = SQLitePlaygroundStore(tmp_path / "playground.db")

    result = import_ai_coding_agents(store, agents_dir=agents_dir)

    assert result.imported == 4
    assert result.updated == 0
    assert set(result.agent_ids_by_role) == set(AI_CODING_ROLES)
    assert len(store.list_agents()) == 4

    rows = _metadata_rows(store)
    assert len(rows) == 4
    assert {row["pipeline_family"] for row in rows} == {"ai_coding"}
    assert {row["role"] for row in rows} == set(AI_CODING_ROLES)


def test_import_ai_coding_agents_is_idempotent(tmp_path: Path) -> None:
    from app.seeds.ai_coding_agents import import_ai_coding_agents

    agents_dir = tmp_path / "agents"
    _write_agent_prompts(agents_dir)
    store = SQLitePlaygroundStore(tmp_path / "playground.db")

    first = import_ai_coding_agents(store, agents_dir=agents_dir)
    second = import_ai_coding_agents(store, agents_dir=agents_dir)

    assert second.imported == 0
    assert second.updated == 4
    assert second.agent_ids_by_role == first.agent_ids_by_role
    assert len(store.list_agents()) == 4
    assert len(_metadata_rows(store)) == 4


def test_imported_ai_coding_agent_can_be_referenced_by_pipeline_stage(tmp_path: Path) -> None:
    from app.seeds.ai_coding_agents import import_ai_coding_agents

    agents_dir = tmp_path / "agents"
    _write_agent_prompts(agents_dir)
    store = SQLitePlaygroundStore(tmp_path / "playground.db")
    imported = import_ai_coding_agents(store, agents_dir=agents_dir)

    pipeline_store = PipelineStore(store.db_path)
    definition = pipeline_store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding",
            kind="sequential_pipeline",
            stages=[
                {
                    "name": "Design",
                    "role": "designer",
                    "agent_id": imported.agent_ids_by_role["designer"],
                    "stage_order": 1,
                }
            ],
        )
    )

    assert definition.stages[0].agent_id == imported.agent_ids_by_role["designer"]
