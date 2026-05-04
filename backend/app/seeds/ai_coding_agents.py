from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from ..schemas import AgentDefinitionCreate, AgentDefinitionUpdate
from ..store import SQLitePlaygroundStore


AI_CODING_AGENT_ROLES = ("designer", "reviewer", "coder", "validator")
AI_CODING_PIPELINE_FAMILY = "ai_coding"
AI_CODING_SOURCE_PROVIDER = "ai_coding_worker_agents"


@dataclass(frozen=True)
class AiCodingAgentImportResult:
    imported: int
    updated: int
    agent_ids_by_role: dict[str, str]


def default_ai_coding_agents_dir() -> Path:
    env_value = os.getenv("AI_CODING_AGENTS_DIR")
    if env_value:
        return Path(env_value).expanduser().resolve()

    repo_root = Path(__file__).resolve().parents[3]
    for parent in (repo_root, *repo_root.parents):
        candidate = parent / "ai_coding" / "worker" / "agents"
        if candidate.exists():
            return candidate.resolve()
    return (repo_root.parent / "ai_coding" / "worker" / "agents").resolve()


def _read_prompt(agents_dir: Path, role: str) -> tuple[str, Path, str]:
    prompt_path = agents_dir / f"{role}.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return prompt, prompt_path.resolve(), source_hash


def _metadata_row(store: SQLitePlaygroundStore, role: str) -> sqlite3.Row | None:
    with closing(store._connect()) as connection:
        return connection.execute(
            """
            SELECT agent_id
            FROM agent_import_metadata
            WHERE pipeline_family = ? AND role = ?
            """,
            (AI_CODING_PIPELINE_FAMILY, role),
        ).fetchone()


def _agent_payload(role: str, prompt: str) -> AgentDefinitionCreate:
    label = role.replace("_", " ").title()
    return AgentDefinitionCreate(
        name=f"AI Coding {label}",
        description=f"Imported ai_coding {role} agent prompt.",
        system_prompt=prompt,
        model=None,
        skill_ids=[],
        builtin_capabilities=["filesystem"],
    )


def _upsert_metadata(
    store: SQLitePlaygroundStore,
    *,
    agent_id: str,
    role: str,
    source_path: Path,
    source_hash: str,
) -> None:
    with closing(store._connect()) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO agent_import_metadata (
                    agent_id, pipeline_family, role, source_provider, source_path, source_hash
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(pipeline_family, role) DO UPDATE SET
                    agent_id = excluded.agent_id,
                    source_provider = excluded.source_provider,
                    source_path = excluded.source_path,
                    source_hash = excluded.source_hash,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    agent_id,
                    AI_CODING_PIPELINE_FAMILY,
                    role,
                    AI_CODING_SOURCE_PROVIDER,
                    str(source_path),
                    source_hash,
                ),
            )


def import_ai_coding_agents(
    store: SQLitePlaygroundStore,
    *,
    agents_dir: Path | None = None,
) -> AiCodingAgentImportResult:
    resolved_agents_dir = (agents_dir or default_ai_coding_agents_dir()).resolve()
    if not resolved_agents_dir.exists():
        raise FileNotFoundError(f"AI Coding agents directory does not exist: {resolved_agents_dir}")

    imported = 0
    updated = 0
    agent_ids_by_role: dict[str, str] = {}

    for role in AI_CODING_AGENT_ROLES:
        prompt, source_path, source_hash = _read_prompt(resolved_agents_dir, role)
        create_payload = _agent_payload(role, prompt)
        existing_metadata = _metadata_row(store, role)
        existing_agent_id = existing_metadata["agent_id"] if existing_metadata else None
        existing_agent = store.get_agent(existing_agent_id) if existing_agent_id else None

        if existing_agent is None:
            agent = store.create_agent(create_payload)
            imported += 1
        else:
            updated_agent = store.update_agent(
                existing_agent.id,
                AgentDefinitionUpdate(**create_payload.model_dump()),
            )
            if updated_agent is None:
                agent = store.create_agent(create_payload)
                imported += 1
            else:
                agent = updated_agent
                updated += 1

        _upsert_metadata(
            store,
            agent_id=agent.id,
            role=role,
            source_path=source_path,
            source_hash=source_hash,
        )
        agent_ids_by_role[role] = agent.id

    return AiCodingAgentImportResult(imported=imported, updated=updated, agent_ids_by_role=agent_ids_by_role)
