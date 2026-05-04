from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.routes_agents as routes_agents
from app.schemas import AgentDefinition, AgentDefinitionCreate, AgentDefinitionUpdate, SkillDefinition


class FakeStore:
    def __init__(self) -> None:
        self.skills = {
            "skill-1": SkillDefinition(
                id="skill-1",
                name="Skill One",
                description="Test skill.",
                instruction="Use it well.",
                source_provider=None,
                source_skill_id=None,
                tool=None,
                local_path=None,
                runtime_preflight=None,
            )
        }
        self.agent = AgentDefinition(
            id="agent-1",
            name="Agent One",
            description="Agent for tests.",
            system_prompt="You are agent one.",
            model="gpt-test",
            skill_ids=[],
            builtin_capabilities=["filesystem"],
        )
        self.deleted_workflows: list[str] = []
        self.deleted_agents: list[str] = []
        self.updated_payloads: list[tuple[str, dict[str, object]]] = []

    def get_skill(self, skill_id: str):
        return self.skills.get(skill_id)

    def list_agents(self):
        return [self.agent]

    def create_agent(self, payload: AgentDefinitionCreate):
        return AgentDefinition(id="agent-created", **payload.model_dump())

    def update_agent(self, agent_id: str, payload: AgentDefinitionUpdate):
        self.updated_payloads.append((agent_id, payload.model_dump()))
        return AgentDefinition(id=agent_id, **payload.model_dump())

    def get_agent(self, agent_id: str):
        if agent_id == self.agent.id:
            return self.agent
        return None

    def agent_usage_workflows(self, agent_id: str):
        return [
            SimpleNamespace(id="workflow-safe", type="single_agent_chat", name="Safe Workflow"),
        ]

    def delete_workflow(self, workflow_id: str):
        self.deleted_workflows.append(workflow_id)
        return True

    def delete_agent(self, agent_id: str):
        self.deleted_agents.append(agent_id)
        return True


def test_agents_route_helpers_cover_validation_and_delete_rules(monkeypatch):
    fake_store = FakeStore()
    monkeypatch.setattr(routes_agents, "store", fake_store)

    routes_agents._validate_skill_ids(["skill-1"])

    with pytest.raises(routes_agents.HTTPException) as error:
        routes_agents._validate_skill_ids(["missing-skill"])
    assert error.value.status_code == 400

    created = routes_agents.create_agent(
        AgentDefinitionCreate(
            name="Created Agent",
            description="Created in route test.",
            system_prompt="You are a created agent.",
            model="gpt-test",
            skill_ids=["skill-1"],
            builtin_capabilities=["filesystem"],
        )
    )
    assert created.id == "agent-created"

    updated = routes_agents.update_agent(
        "agent-1",
        AgentDefinitionUpdate(
            name="Updated Agent",
            description="Updated route test agent.",
            system_prompt="You are updated.",
            model="gpt-test",
            skill_ids=["skill-1"],
            builtin_capabilities=["filesystem"],
        ),
    )
    assert updated.name == "Updated Agent"

    deleted = routes_agents.delete_agent("agent-1")
    assert deleted == {"deleted": True}
    assert fake_store.deleted_workflows == ["workflow-safe"]

    with pytest.raises(routes_agents.HTTPException) as missing_error:
        routes_agents.delete_agent("missing-agent")
    assert missing_error.value.status_code == 404
