from __future__ import annotations

import sqlite3


def ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    ddl_fragment: str,
) -> None:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_fragment}")


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            model TEXT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ensure_column(
        connection,
        "agents",
        "skill_ids",
        "TEXT NOT NULL DEFAULT '[]'",
    )
    ensure_column(
        connection,
        "agents",
        "builtin_capabilities",
        "TEXT NOT NULL DEFAULT '[]'",
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            specialist_agent_ids TEXT NOT NULL,
            router_prompt TEXT NOT NULL,
            finalizer_enabled INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            instruction TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ensure_column(
        connection,
        "skills",
        "source_provider",
        "TEXT NULL",
    )
    ensure_column(
        connection,
        "skills",
        "source_skill_id",
        "TEXT NULL",
    )
    ensure_column(
        connection,
        "skills",
        "local_path",
        "TEXT NULL",
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_skills_source_unique
        ON skills(source_provider, source_skill_id)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            title TEXT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_name TEXT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
        ON messages(conversation_id)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_definitions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            description TEXT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_stage_definitions (
            id TEXT PRIMARY KEY,
            pipeline_id TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            stage_order INTEGER NOT NULL,
            retry_limit INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (pipeline_id) REFERENCES pipeline_definitions(id),
            UNIQUE (pipeline_id, stage_order)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_stage_definitions_pipeline_id
        ON pipeline_stage_definitions(pipeline_id, stage_order)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id TEXT PRIMARY KEY,
            pipeline_id TEXT NOT NULL,
            title TEXT NOT NULL,
            source_prd_id TEXT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            current_stage_id TEXT NULL,
            input_payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pipeline_id) REFERENCES pipeline_definitions(id),
            FOREIGN KEY (current_stage_id) REFERENCES pipeline_stage_definitions(id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_runs_pipeline_id
        ON pipeline_runs(pipeline_id)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_stage_runs (
            id TEXT PRIMARY KEY,
            pipeline_run_id TEXT NOT NULL,
            stage_definition_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempt INTEGER NOT NULL DEFAULT 0,
            input_payload TEXT NOT NULL DEFAULT '{}',
            output_payload TEXT NOT NULL DEFAULT '{}',
            error_message TEXT NULL,
            started_at TEXT NULL,
            completed_at TEXT NULL,
            FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(id),
            FOREIGN KEY (stage_definition_id) REFERENCES pipeline_stage_definitions(id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_stage_runs_pipeline_run_id
        ON pipeline_stage_runs(pipeline_run_id)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_artifacts (
            id TEXT PRIMARY KEY,
            pipeline_run_id TEXT NOT NULL,
            stage_run_id TEXT NULL,
            artifact_type TEXT NOT NULL,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(id),
            FOREIGN KEY (stage_run_id) REFERENCES pipeline_stage_runs(id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_artifacts_pipeline_run_id
        ON pipeline_artifacts(pipeline_run_id)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
