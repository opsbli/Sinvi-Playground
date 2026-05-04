from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from ..schemas import AgentDefinitionCreate, AgentDefinitionUpdate
from ..store import SQLitePlaygroundStore


PIPELINE_FAMILY = "ai_coding"
SOURCE_PROVIDER = "builtin_pipeline_prd_story_agents"


PROMPTS_BY_ROLE = {
    "prd_writer": (
        "You are the PRD Writer for the AI Coding pipeline. Convert a concise product brief into a "
        "structured PRD with goals, users, scope, requirements, non-goals, risks, and acceptance criteria."
    ),
    "story_splitter": (
        "You are the Story Splitter for the AI Coding pipeline. Convert a PRD into small, ordered user "
        "stories with clear titles, value statements, acceptance criteria, dependencies, and boundaries."
    ),
}


@dataclass(frozen=True)
class PrdStoryAgentSeedResult:
    imported: int
    updated: int
    agent_ids_by_role: dict[str, str]


def _metadata_row(store: SQLitePlaygroundStore, role: str) -> sqlite3.Row | None:
    with closing(store._connect()) as connection:
        return connection.execute(
            """
            SELECT agent_id
            FROM agent_import_metadata
            WHERE pipeline_family = ? AND role = ?
            """,
            (PIPELINE_FAMILY, role),
        ).fetchone()


def _upsert_metadata(store: SQLitePlaygroundStore, *, agent_id: str, role: str, prompt: str) -> None:
    source_path = f"builtin://{PIPELINE_FAMILY}/{role}"
    source_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
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
                (agent_id, PIPELINE_FAMILY, role, SOURCE_PROVIDER, source_path, source_hash),
            )


def _payload(role: str, prompt: str) -> AgentDefinitionCreate:
    label = role.replace("_", " ").title()
    return AgentDefinitionCreate(
        name=f"AI Coding {label}",
        description=f"Built-in {role} agent for PRD/story generation.",
        system_prompt=prompt,
        model=None,
        skill_ids=[],
        builtin_capabilities=["filesystem"],
    )


def seed_prd_story_agents(store: SQLitePlaygroundStore) -> PrdStoryAgentSeedResult:
    imported = 0
    updated = 0
    agent_ids_by_role: dict[str, str] = {}

    for role, prompt in PROMPTS_BY_ROLE.items():
        payload = _payload(role, prompt)
        row = _metadata_row(store, role)
        existing_id = row["agent_id"] if row else None
        existing_agent = store.get_agent(existing_id) if existing_id else None

        if existing_agent is None:
            agent = store.create_agent(payload)
            imported += 1
        else:
            agent = store.update_agent(existing_agent.id, AgentDefinitionUpdate(**payload.model_dump()))
            if agent is None:
                agent = store.create_agent(payload)
                imported += 1
            else:
                updated += 1

        _upsert_metadata(store, agent_id=agent.id, role=role, prompt=prompt)
        agent_ids_by_role[role] = agent.id

    return PrdStoryAgentSeedResult(imported=imported, updated=updated, agent_ids_by_role=agent_ids_by_role)
