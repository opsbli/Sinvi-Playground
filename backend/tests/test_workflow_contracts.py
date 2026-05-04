from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.app.runtime import llm_gateway
from backend.app.schemas import AgentDefinitionCreate, WorkflowDefinitionCreate
from backend.app.store import SQLitePlaygroundStore
import backend.app.workflows.peer_handoff.workflow as peer_workflow
import backend.app.workflows.planner_executor.workflow as planner_workflow
import backend.app.workflows.single_agent_chat.workflow as single_workflow
import backend.app.workflows.supervisor_dynamic.workflow as supervisor_workflow


@dataclass(frozen=True)
class WorkflowCase:
    workflow_type: str
    run_func: object
    module: object
    agent_count: int


CASES = (
    WorkflowCase("single_agent_chat", single_workflow.run_single_agent_chat, single_workflow, 1),
    WorkflowCase("planner_executor", planner_workflow.run_planner_executor, planner_workflow, 2),
    WorkflowCase("supervisor_dynamic", supervisor_workflow.run_supervisor_dynamic, supervisor_workflow, 2),
    WorkflowCase("peer_handoff", peer_workflow.run_peer_handoff, peer_workflow, 2),
)


def _build_store() -> SQLitePlaygroundStore:
    return SQLitePlaygroundStore()


def _seed_agents(store: SQLitePlaygroundStore, count: int) -> list[str]:
    agent_ids: list[str] = []
    for index in range(count):
        agent = store.create_agent(
            AgentDefinitionCreate(
                name=f"Agent {index + 1}",
                description=f"Agent {index + 1} description.",
                system_prompt=f"You are Agent {index + 1}.",
            )
        )
        agent_ids.append(agent.id)
    return agent_ids


def _make_run_agent_stub():
    def fake_run_agent(agent, user_input, **kwargs):
        if kwargs.get("response_contract") == "action_json":
            return '{"action":"complete","message":"Completed the peer task."}'
        return f"{agent.name} response for: {user_input}"

    return fake_run_agent


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.workflow_type)
def test_workflow_runs_expose_minimal_response_contract(monkeypatch: pytest.MonkeyPatch, case: WorkflowCase) -> None:
    store = _build_store()
    agent_ids = _seed_agents(store, case.agent_count)
    workflow = store.create_workflow(
        WorkflowDefinitionCreate(
            name=f"{case.workflow_type} workflow",
            type=case.workflow_type,  # type: ignore[arg-type]
            specialist_agent_ids=agent_ids,
            finalizer_enabled=True,
        )
    )

    def raise_no_api(*_args, **_kwargs):
        raise RuntimeError("OpenAI API not configured")

    monkeypatch.setattr(case.module, "call_llm", raise_no_api)
    monkeypatch.setattr(llm_gateway, "run_agent", _make_run_agent_stub())

    response = case.run_func(store, workflow, "Validate the workflow contract.")

    assert response.workflow_id == workflow.id
    assert response.user_input == "Validate the workflow contract."
    assert response.assistant_message
    assert response.artifacts.final_answer == response.assistant_message
    assert response.trace, "expected a non-empty trace"
    assert response.trace[0].type == "run_started"
    assert response.trace[-1].type == "run_finished"
    assert response.graph.nodes, "expected a populated workflow graph"
    assert response.graph.edges, "expected a populated workflow graph"
    assert any(node.id == "start" for node in response.graph.nodes)
    assert any(node.id == "end" for node in response.graph.nodes)

