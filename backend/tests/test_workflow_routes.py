from __future__ import annotations

from types import SimpleNamespace

import importlib

import pytest
from fastapi import HTTPException

from app.schemas import WorkflowDefinition, WorkflowDefinitionCreate, WorkflowDefinitionUpdate


def _load_module():
    return importlib.import_module("app.routes_workflows")


class FakeStore:
    def __init__(self) -> None:
        self.templates = [
            SimpleNamespace(type="router_specialists", required_agent_count=2),
            SimpleNamespace(type="single_agent_chat", required_agent_count=1),
        ]
        self.agents = {
            "agent-1": SimpleNamespace(id="agent-1", name="Agent 1"),
            "agent-2": SimpleNamespace(id="agent-2", name="Agent 2"),
        }
        self.workflow = WorkflowDefinition(
            id="workflow-1",
            name="Workflow",
            type="router_specialists",
            specialist_agent_ids=["agent-1", "agent-2"],
            router_prompt="Route well.",
            finalizer_enabled=True,
        )

    def get_templates(self):
        return self.templates

    def get_agent(self, agent_id: str):
        return self.agents.get(agent_id)

    def create_workflow(self, payload):
        data = payload.model_dump()
        return WorkflowDefinition(id="workflow-created", **data)

    def update_workflow(self, workflow_id: str, payload):
        if workflow_id != self.workflow.id:
            return None
        data = payload.model_dump()
        return WorkflowDefinition(id=workflow_id, **data)

    def get_workflow(self, workflow_id: str):
        if workflow_id == self.workflow.id:
            return self.workflow
        return None

    def delete_workflow(self, workflow_id: str):
        return workflow_id == self.workflow.id

    def list_workflows(self):
        return [self.workflow]


def test_create_workflow_rejects_insufficient_agents(api_client, monkeypatch):
    module = _load_module()
    fake_store = FakeStore()
    monkeypatch.setattr(module, "store", fake_store)

    payload = WorkflowDefinitionCreate(
        name="Workflow",
        type="router_specialists",
        specialist_agent_ids=["agent-1"],
        router_prompt="Route well.",
        finalizer_enabled=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        module.create_workflow(payload)

    assert exc_info.value.status_code == 400
    assert "requires at least 2 agents" in str(exc_info.value.detail)


def test_get_workflow_graph_dispatches_by_type(api_client, monkeypatch):
    module = _load_module()
    fake_store = FakeStore()
    fake_store.workflow = WorkflowDefinition(
        id="workflow-1",
        name="Workflow",
        type="router_specialists",
        specialist_agent_ids=["agent-1", "missing-agent"],
        router_prompt="Route well.",
        finalizer_enabled=True,
    )
    monkeypatch.setattr(module, "store", fake_store)

    captured = {}

    def fake_build_router_graph(workflow, agents):  # noqa: ANN001
        captured["workflow_id"] = workflow.id
        captured["agent_ids"] = [agent.id for agent in agents]
        return {"nodes": [], "edges": []}

    monkeypatch.setattr(module, "build_router_graph", fake_build_router_graph)

    result = module.get_workflow_graph("workflow-1")

    assert result == {"nodes": [], "edges": []}
    assert captured == {"workflow_id": "workflow-1", "agent_ids": ["agent-1"]}
