from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .schemas import (
    AgentDefinition,
    AppSettings,
    ConversationCreate,
    TraceEvent,
    WorkflowDefinition,
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowGraph,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from .settings_bridge import (
    apply_structured_settings,
    normalize_structured_settings,
    settings,
)
from .routes_agents import router as agents_router
from .routes_conversations import router as conversations_router
from .routes_skills import router as skills_router
from .runtime import llm_gateway
from .store import store
from .workflows.planner_executor.workflow import build_planner_graph, run_planner_executor
from .workflows.peer_handoff.workflow import build_peer_handoff_graph, run_peer_handoff
from .workflows.router_specialists.workflow import build_router_graph, run_router_specialists
from .workflows.single_agent_chat.workflow import build_single_agent_graph, run_single_agent_chat
from .workflows.supervisor_dynamic.workflow import build_supervisor_graph, run_supervisor_dynamic


router = APIRouter(prefix="/api")
router.include_router(agents_router)
router.include_router(skills_router)
router.include_router(conversations_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/settings", response_model=AppSettings)
def get_app_settings() -> AppSettings:
    structured = normalize_structured_settings(store.get_app_settings_payload())
    return AppSettings(
        model_profiles=structured["model_profiles"],  # type: ignore[arg-type]
        active_model_profile_id=str(structured["active_model_profile_id"] or "") or None,
        env_vars=structured["env_vars"],  # type: ignore[arg-type]
        env_path=settings.APP_ENV_PATH,
    )


@router.put("/settings", response_model=AppSettings)
def update_app_settings(payload: AppSettings) -> AppSettings:
    previous = store.get_app_settings_payload()
    current = normalize_structured_settings(payload.model_dump())
    store.save_app_settings_payload(current)
    apply_structured_settings(previous, current)
    llm_gateway.refresh_client()
    structured = normalize_structured_settings(store.get_app_settings_payload())
    return AppSettings(
        model_profiles=structured["model_profiles"],  # type: ignore[arg-type]
        active_model_profile_id=str(structured["active_model_profile_id"] or "") or None,
        env_vars=structured["env_vars"],  # type: ignore[arg-type]
        env_path=settings.APP_ENV_PATH,
    )


@router.get("/workflow-templates")
def list_workflow_templates():
    return store.get_templates()


@router.get("/workflows", response_model=list[WorkflowDefinition])
def list_workflows() -> list[WorkflowDefinition]:
    return store.list_workflows()


def _required_agent_count(workflow_type: str) -> int:
    for template in store.get_templates():
        if template.type == workflow_type:
            return template.required_agent_count
    return 2


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


def _dispatch_run(
    workflow: WorkflowDefinition,
    user_input: str,
    conversation_id: str | None = None,
    on_event: Callable[[TraceEvent], None] | None = None,
) -> WorkflowRunResponse:
    history = []
    if conversation_id:
        recent = store.get_recent_messages(conversation_id, limit=2)
        history = [{"role": msg.role, "content": msg.content} for msg in recent]

    if workflow.type == "router_specialists":
        return run_router_specialists(store, workflow, user_input, history=history, on_event=on_event)
    if workflow.type == "planner_executor":
        return run_planner_executor(store, workflow, user_input, history=history, on_event=on_event)
    if workflow.type == "supervisor_dynamic":
        return run_supervisor_dynamic(store, workflow, user_input, history=history, on_event=on_event)
    if workflow.type == "single_agent_chat":
        return run_single_agent_chat(store, workflow, user_input, history=history, on_event=on_event)
    if workflow.type == "peer_handoff":
        return run_peer_handoff(store, workflow, user_input, history=history, on_event=on_event)
    raise HTTPException(status_code=400, detail=f"Unsupported workflow type: {workflow.type}")


@router.post("/runs", response_model=WorkflowRunResponse)
def run_workflow(payload: WorkflowRunRequest) -> WorkflowRunResponse:
    workflow = store.get_workflow(payload.workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    conversation_id = payload.conversation_id
    if not conversation_id:
        conversation = store.create_conversation(
            ConversationCreate(workflow_id=payload.workflow_id)
        )
        conversation_id = conversation.id

    result = _dispatch_run(workflow, payload.user_input, conversation_id=conversation_id)

    store.create_message(
        conversation_id=conversation_id,
        role="user",
        content=payload.user_input,
    )
    store.create_message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.assistant_message,
        agent_name=result.artifacts.route_agent_name,
    )

    if store.get_conversation(conversation_id).title is None:
        title = payload.user_input[:50] + ("..." if len(payload.user_input) > 50 else "")
        store.update_conversation_title(conversation_id, title)

    result.conversation_id = conversation_id
    return result


@router.post("/runs/stream")
def run_workflow_stream(payload: WorkflowRunRequest) -> StreamingResponse:
    workflow = store.get_workflow(payload.workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    conversation_id = payload.conversation_id
    if not conversation_id:
        conversation = store.create_conversation(
            ConversationCreate(workflow_id=payload.workflow_id)
        )
        conversation_id = conversation.id

    stream_queue: queue.Queue[tuple[str, dict | None]] = queue.Queue()

    def on_trace(event: TraceEvent) -> None:
        stream_queue.put(("trace", event.model_dump()))

    def worker() -> None:
        try:
            result = _dispatch_run(workflow, payload.user_input, conversation_id=conversation_id, on_event=on_trace)

            store.create_message(
                conversation_id=conversation_id,
                role="user",
                content=payload.user_input,
            )
            store.create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=result.assistant_message,
                agent_name=result.artifacts.route_agent_name,
            )

            if store.get_conversation(conversation_id).title is None:
                title = payload.user_input[:50] + ("..." if len(payload.user_input) > 50 else "")
                store.update_conversation_title(conversation_id, title)

            result.conversation_id = conversation_id
            stream_queue.put(("final", result.model_dump()))
        except Exception as error:  # noqa: BLE001
            stream_queue.put(("error", {"message": str(error)}))
        finally:
            stream_queue.put(("end", None))

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            event_name, body = stream_queue.get()
            if event_name == "end":
                yield "event: end\ndata: {}\n\n"
                break
            yield f"event: {event_name}\ndata: {json.dumps(body, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


