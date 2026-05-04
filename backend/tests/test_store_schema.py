from __future__ import annotations

import sqlite3

from app.store_schema import initialize_schema


def test_initialize_schema_creates_core_tables_and_indexes() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        initialize_schema(connection)

        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
            ).fetchall()
        }
        assert {"agents", "workflows", "skills", "conversations", "messages", "app_settings"}.issubset(
            tables
        )
        assert "idx_skills_source_unique" in tables
        assert "idx_messages_conversation_id" in tables

        agent_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(agents)").fetchall()
        }
        assert {"skill_ids", "builtin_capabilities"}.issubset(agent_columns)

        skill_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(skills)").fetchall()
        }
        assert {"source_provider", "source_skill_id", "local_path"}.issubset(skill_columns)
    finally:
        connection.close()
