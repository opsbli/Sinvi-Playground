from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import AgentDefinition, WorkflowDefinition, WorkflowDefinitionCreate, WorkflowDefinitionUpdate, WorkflowGraph
from .store import store
from .workflows.planner_executor.workflow import build_planner_graph
from .workflows.peer_handoff.workflow import build_peer_handoff_graph
from .workflows.router_specialists.workflow import build_router_graph
from .workflows.single_agent_chat.workflow import build_single_agent_graph
from .workflows.supervisor_dynamic.workflow import build_supervisor_graph


router = APIRouter()


def _required_agent_count(workflow_type: str) -> int:
    for template in store.get_templates():
        if template.type == workflow_type:
            return template.required_agent_count
    return 2


@router.get("/workflows", response_model=list[WorkflowDefinition])
def list_workflows() -> list[WorkflowDefinition]:
    return store.list_workflows()


@router.post("/workflows", response_model=WorkflowDefinition)
def create_workflow(payload: WorkflowDefinitionCreate) -> WorkflowDefinition:
    missing_ids = [agent_id for agent_id in payload.specialist_agent_ids if store.get_agent(agent_id) is None]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"These agent IDs do not exist: {missing_ids}")

    required_count = _required_agent_count(payload.type)
    if len(payload.specialist_agent_ids) < required_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{payload.type} requires at least {required_count} agents, "
                f"but got {len(payload.specialist_agent_ids)}."
            ),
        )
    return store.create_workflow(payload)


@router.put("/workflows/{workflow_id}", response_model=WorkflowDefinition)
def update_workflow(workflow_id: str, payload: WorkflowDefinitionUpdate) -> WorkflowDefinition:
    missing_ids = [agent_id for agent_id in payload.specialist_agent_ids if store.get_agent(agent_id) is None]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"These agent IDs do not exist: {missing_ids}")

    required_count = _required_agent_count(payload.type)
    if len(payload.specialist_agent_ids) < required_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{payload.type} requires at least {required_count} agents, "
                f"but got {len(payload.specialist_agent_ids)}."
            ),
        )

    updated = store.update_workflow(workflow_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return updated


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: str) -> dict[str, bool]:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    deleted = store.delete_workflow(workflow_id)
    return {"deleted": deleted}


def _resolve_agents(workflow: WorkflowDefinition) -> list[AgentDefinition]:
    agents = [store.get_agent(agent_id) for agent_id in workflow.specialist_agent_ids]
    return [agent for agent in agents if agent is not None]


@router.get("/workflows/{workflow_id}/graph", response_model=WorkflowGraph)
def get_workflow_graph(workflow_id: str) -> WorkflowGraph:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    agents = _resolve_agents(workflow)
    if workflow.type == "router_specialists":
        return build_router_graph(workflow, agents)
    if workflow.type == "planner_executor":
        return build_planner_graph(workflow, agents)
    if workflow.type == "supervisor_dynamic":
        return build_supervisor_graph(workflow, agents)
    if workflow.type == "single_agent_chat":
        return build_single_agent_graph(workflow, agents)
    if workflow.type == "peer_handoff":
        return build_peer_handoff_graph(workflow, agents)

    raise HTTPException(status_code=400, detail=f"Unsupported workflow type: {workflow.type}")
