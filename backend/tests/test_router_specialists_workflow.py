from __future__ import annotations

import pytest

from backend.app.runtime import llm_gateway
from backend.app.schemas import AgentDefinitionCreate, WorkflowDefinitionCreate
from backend.app.store import SQLitePlaygroundStore
import backend.app.workflows.router_specialists.workflow as router_workflow
from backend.app.workflows.router_specialists.workflow import run_router_specialists


def _build_store() -> SQLitePlaygroundStore:
    return SQLitePlaygroundStore()


def _seed_router_workflow(store: SQLitePlaygroundStore):
    first = store.create_agent(
        AgentDefinitionCreate(
            name="Alpha Specialist",
            description="Handles general implementation checks.",
            system_prompt="You are Alpha.",
        )
    )
    second = store.create_agent(
        AgentDefinitionCreate(
            name="Beta Specialist",
            description="Handles documentation checks.",
            system_prompt="You are Beta.",
        )
    )
    workflow = store.create_workflow(
        WorkflowDefinitionCreate(
            name="Router",
            type="router_specialists",
            specialist_agent_ids=[first.id, second.id],
            finalizer_enabled=True,
        )
    )
    return workflow, first, second


def test_router_specialists_fallback_returns_route_selected_and_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _build_store()
    workflow, first, _second = _seed_router_workflow(store)

    def raise_no_api(*_args, **_kwargs):
        raise RuntimeError("OpenAI API not configured")

    def fake_run_agent(agent, user_input, **kwargs):
        if kwargs.get("response_contract") == "action_json":
            return '{"action":"complete","message":"Finished the workflow."}'
        return f"{agent.name} handled: {user_input}"

    monkeypatch.setattr(router_workflow, "call_llm", raise_no_api)
    monkeypatch.setattr(llm_gateway, "run_agent", fake_run_agent)

    response = run_router_specialists(store, workflow, "Please validate the workflow fallback path.")

    route_events = [event for event in response.trace if event.type == "route_selected"]
    assert route_events, "expected the router to record a route_selected event"
    assert route_events[0].payload["next_node_id"] == first.id
    assert response.artifacts.route_agent_id == first.id
    assert response.artifacts.route_agent_name == first.name
    assert response.artifacts.route_reason
    assert response.artifacts.specialist_answer
    assert response.artifacts.final_answer == response.assistant_message
    assert response.trace[0].type == "run_started"
    assert response.trace[-1].type == "run_finished"
    assert response.graph.nodes
    assert response.graph.edges

