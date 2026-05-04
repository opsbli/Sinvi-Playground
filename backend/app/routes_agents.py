from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import AgentDefinition, AgentDefinitionCreate, AgentDefinitionUpdate
from .store import store


router = APIRouter()


def _validate_skill_ids(skill_ids: list[str]) -> None:
    missing_ids = [skill_id for skill_id in skill_ids if store.get_skill(skill_id) is None]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"These skill IDs do not exist: {missing_ids}")


@router.get("/agents", response_model=list[AgentDefinition])
def list_agents() -> list[AgentDefinition]:
    return store.list_agents()


@router.post("/agents", response_model=AgentDefinition)
def create_agent(payload: AgentDefinitionCreate) -> AgentDefinition:
    _validate_skill_ids(payload.skill_ids)
    return store.create_agent(payload)


@router.put("/agents/{agent_id}", response_model=AgentDefinition)
def update_agent(agent_id: str, payload: AgentDefinitionUpdate) -> AgentDefinition:
    _validate_skill_ids(payload.skill_ids)
    updated = store.update_agent(agent_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return updated


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str) -> dict[str, bool]:
    agent = store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    usage = store.agent_usage_workflows(agent_id)
    blocking = [w for w in usage if w.type != "single_agent_chat"]
    if blocking:
        names = ", ".join(workflow.name for workflow in blocking[:5])
        raise HTTPException(
            status_code=409,
            detail=f"Agent is still used by workflow(s): {names}",
        )

    for workflow in usage:
        if workflow.type == "single_agent_chat":
            store.delete_workflow(workflow.id)

    deleted = store.delete_agent(agent_id)
    return {"deleted": deleted}
