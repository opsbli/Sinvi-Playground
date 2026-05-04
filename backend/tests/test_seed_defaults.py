from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.schemas import AgentDefinitionCreate, WorkflowDefinitionCreate
from app.store import SQLitePlaygroundStore


DEFAULT_AGENT_NAMES = ("产品经理", "设计师", "工程师")


def _agent_name_counts(store: SQLitePlaygroundStore) -> Counter[str]:
    return Counter(agent.name for agent in store.list_agents())


def _workflow_key_counts(store: SQLitePlaygroundStore) -> Counter[tuple[str, str]]:
    return Counter((workflow.name, workflow.type) for workflow in store.list_workflows())


def test_seed_defaults_backfills_default_agents_when_other_agents_exist(tmp_path: Path) -> None:
    store = SQLitePlaygroundStore(tmp_path / "playground.db")
    store.create_agent(
        AgentDefinitionCreate(
            name="Custom Agent",
            description="User-owned agent.",
            system_prompt="Keep this user-owned agent.",
        )
    )

    store.seed_defaults()

    counts = _agent_name_counts(store)
    assert counts["Custom Agent"] == 1
    for name in DEFAULT_AGENT_NAMES:
        assert counts[name] == 1


def test_seed_defaults_does_not_duplicate_default_agents_on_repeated_startup(tmp_path: Path) -> None:
    store = SQLitePlaygroundStore(tmp_path / "playground.db")

    store.seed_defaults()
    store.seed_defaults()

    counts = _agent_name_counts(store)
    for name in DEFAULT_AGENT_NAMES:
        assert counts[name] == 1


def test_seed_defaults_collapses_known_demo_workflow_duplicates(tmp_path: Path) -> None:
    store = SQLitePlaygroundStore(tmp_path / "playground.db")
    agent = store.create_agent(
        AgentDefinitionCreate(
            name="Agent 1",
            description="Demo agent.",
            system_prompt="Demo agent prompt.",
        )
    )
    for _ in range(2):
        store.create_workflow(
            WorkflowDefinitionCreate(
                name="Router",
                type="router_specialists",
                specialist_agent_ids=[agent.id],
            )
        )
        store.create_workflow(
            WorkflowDefinitionCreate(
                name="planner_executor workflow",
                type="planner_executor",
                specialist_agent_ids=[agent.id],
            )
        )
    store.create_workflow(
        WorkflowDefinitionCreate(
            name="Router",
            type="single_agent_chat",
            specialist_agent_ids=[agent.id],
        )
    )
    store.create_workflow(
        WorkflowDefinitionCreate(
            name="User workflow",
            type="router_specialists",
            specialist_agent_ids=[agent.id],
        )
    )

    store.seed_defaults()

    counts = _workflow_key_counts(store)
    assert counts[("Router", "router_specialists")] == 1
    assert counts[("planner_executor workflow", "planner_executor")] == 1
    assert counts[("Router", "single_agent_chat")] == 1
    assert counts[("User workflow", "router_specialists")] == 1
