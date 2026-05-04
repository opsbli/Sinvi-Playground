from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .pipeline_schemas import (
    PipelineArtifact,
    PipelineDefinition,
    PipelineDefinitionCreate,
    PipelineRun,
    PipelineRunCreate,
    PipelineStageDefinition,
    PipelineStageRun,
)
from .settings_bridge import settings
from .store_schema import initialize_schema


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _json_loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


class PipelineStore:
    def __init__(self, db_path: Path | None = None) -> None:
        app_home = Path(settings.APP_HOME).resolve()
        self.db_path = db_path or (app_home / "data" / "agent_playground.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def _row_to_stage_definition(self, row: sqlite3.Row) -> PipelineStageDefinition:
        return PipelineStageDefinition(
            id=row["id"],
            pipeline_id=row["pipeline_id"],
            name=row["name"],
            role=row["role"],
            agent_id=row["agent_id"],
            stage_order=row["stage_order"],
            retry_limit=row["retry_limit"],
        )

    def _list_stage_definitions(self, connection: sqlite3.Connection, pipeline_id: str) -> list[PipelineStageDefinition]:
        rows = connection.execute(
            """
            SELECT id, pipeline_id, name, role, agent_id, stage_order, retry_limit
            FROM pipeline_stage_definitions
            WHERE pipeline_id = ?
            ORDER BY stage_order ASC
            """,
            (pipeline_id,),
        ).fetchall()
        return [self._row_to_stage_definition(row) for row in rows]

    def _row_to_definition(self, connection: sqlite3.Connection, row: sqlite3.Row) -> PipelineDefinition:
        return PipelineDefinition(
            id=row["id"],
            name=row["name"],
            kind=row["kind"],
            description=row["description"],
            stages=self._list_stage_definitions(connection, row["id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_stage_run(self, row: sqlite3.Row) -> PipelineStageRun:
        return PipelineStageRun(
            id=row["id"],
            pipeline_run_id=row["pipeline_run_id"],
            stage_definition_id=row["stage_definition_id"],
            status=row["status"],
            attempt=row["attempt"],
            input_payload=_json_loads(row["input_payload"]),
            output_payload=_json_loads(row["output_payload"]),
            error_message=row["error_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def _list_stage_runs(self, connection: sqlite3.Connection, pipeline_run_id: str) -> list[PipelineStageRun]:
        rows = connection.execute(
            """
            SELECT sr.id, sr.pipeline_run_id, sr.stage_definition_id, sr.status, sr.attempt,
                   sr.input_payload, sr.output_payload, sr.error_message, sr.started_at, sr.completed_at
            FROM pipeline_stage_runs sr
            JOIN pipeline_stage_definitions sd ON sd.id = sr.stage_definition_id
            WHERE sr.pipeline_run_id = ?
            ORDER BY sd.stage_order ASC
            """,
            (pipeline_run_id,),
        ).fetchall()
        return [self._row_to_stage_run(row) for row in rows]

    def _row_to_artifact(self, row: sqlite3.Row) -> PipelineArtifact:
        return PipelineArtifact(
            id=row["id"],
            pipeline_run_id=row["pipeline_run_id"],
            stage_run_id=row["stage_run_id"],
            artifact_type=row["artifact_type"],
            name=row["name"],
            content=row["content"],
            metadata=_json_loads(row["metadata"]),
            created_at=row["created_at"],
        )

    def _list_artifacts(self, connection: sqlite3.Connection, pipeline_run_id: str) -> list[PipelineArtifact]:
        rows = connection.execute(
            """
            SELECT id, pipeline_run_id, stage_run_id, artifact_type, name, content, metadata, created_at
            FROM pipeline_artifacts
            WHERE pipeline_run_id = ?
            ORDER BY created_at ASC
            """,
            (pipeline_run_id,),
        ).fetchall()
        return [self._row_to_artifact(row) for row in rows]

    def create_pipeline_artifact(
        self,
        pipeline_run_id: str,
        *,
        artifact_type: str,
        name: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        stage_run_id: str | None = None,
    ) -> PipelineArtifact:
        artifact_id = _new_id("partifact")
        now = _utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pipeline_artifacts (
                    id, pipeline_run_id, stage_run_id, artifact_type, name, content, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    pipeline_run_id,
                    stage_run_id,
                    artifact_type,
                    name,
                    content,
                    _json_dumps(metadata or {}),
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT id, pipeline_run_id, stage_run_id, artifact_type, name, content, metadata, created_at
                FROM pipeline_artifacts
                WHERE id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("Pipeline artifact was not persisted.")
        return self._row_to_artifact(row)

    def _row_to_run(self, connection: sqlite3.Connection, row: sqlite3.Row) -> PipelineRun:
        return PipelineRun(
            id=row["id"],
            pipeline_id=row["pipeline_id"],
            title=row["title"],
            source_prd_id=row["source_prd_id"],
            status=row["status"],
            current_stage_id=row["current_stage_id"],
            input_payload=_json_loads(row["input_payload"]),
            stage_runs=self._list_stage_runs(connection, row["id"]),
            artifacts=self._list_artifacts(connection, row["id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_pipeline_definition(self, payload: PipelineDefinitionCreate) -> PipelineDefinition:
        pipeline_id = _new_id("pipe")
        now = _utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pipeline_definitions (id, name, kind, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pipeline_id, payload.name, payload.kind, payload.description, now, now),
            )
            for stage in sorted(payload.stages, key=lambda item: item.stage_order):
                connection.execute(
                    """
                    INSERT INTO pipeline_stage_definitions
                        (id, pipeline_id, name, role, agent_id, stage_order, retry_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _new_id("pstage"),
                        pipeline_id,
                        stage.name,
                        stage.role,
                        stage.agent_id,
                        stage.stage_order,
                        stage.retry_limit,
                    ),
                )
        definition = self.get_pipeline_definition(pipeline_id)
        if definition is None:
            raise RuntimeError("Pipeline definition was not persisted.")
        return definition

    def list_pipeline_definitions(self) -> list[PipelineDefinition]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, kind, description, created_at, updated_at
                FROM pipeline_definitions
                ORDER BY created_at DESC
                """
            ).fetchall()
            return [self._row_to_definition(connection, row) for row in rows]

    def get_pipeline_definition(self, pipeline_id: str) -> PipelineDefinition | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, kind, description, created_at, updated_at
                FROM pipeline_definitions
                WHERE id = ?
                """,
                (pipeline_id,),
            ).fetchone()
            return self._row_to_definition(connection, row) if row else None

    def create_pipeline_run(self, pipeline_id: str, payload: PipelineRunCreate) -> PipelineRun:
        definition = self.get_pipeline_definition(pipeline_id)
        if definition is None:
            raise ValueError("Pipeline definition not found.")

        run_id = _new_id("prun")
        now = _utc_now_iso()
        current_stage_id = definition.stages[0].id if definition.stages else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pipeline_runs
                    (id, pipeline_id, title, source_prd_id, status, current_stage_id,
                     input_payload, created_at, updated_at)
                VALUES (?, ?, ?, NULL, 'pending', ?, ?, ?, ?)
                """,
                (run_id, pipeline_id, payload.title, current_stage_id, _json_dumps(payload.input_payload), now, now),
            )
            for stage in definition.stages:
                connection.execute(
                    """
                    INSERT INTO pipeline_stage_runs
                        (id, pipeline_run_id, stage_definition_id, status, attempt, input_payload, output_payload)
                    VALUES (?, ?, ?, 'pending', 0, '{}', '{}')
                    """,
                    (_new_id("psrun"), run_id, stage.id),
                )
        run = self.get_pipeline_run(run_id)
        if run is None:
            raise RuntimeError("Pipeline run was not persisted.")
        return run

    def get_pipeline_run(self, run_id: str) -> PipelineRun | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, pipeline_id, title, source_prd_id, status, current_stage_id,
                       input_payload, created_at, updated_at
                FROM pipeline_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
            return self._row_to_run(connection, row) if row else None
