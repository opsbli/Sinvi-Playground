from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .schemas import ConversationCreate, TraceEvent, WorkflowDefinition, WorkflowRunRequest, WorkflowRunResponse
from .store import store
from .workflows.peer_handoff.workflow import run_peer_handoff
from .workflows.planner_executor.workflow import run_planner_executor
from .workflows.router_specialists.workflow import run_router_specialists
from .workflows.single_agent_chat.workflow import run_single_agent_chat
from .workflows.supervisor_dynamic.workflow import run_supervisor_dynamic


router = APIRouter()


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
