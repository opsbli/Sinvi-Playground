from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import Conversation, ConversationCreate, ConversationDetail
from .store import store


router = APIRouter()


@router.get("/conversations", response_model=list[Conversation])
def list_conversations(workflow_id: str | None = None) -> list[Conversation]:
    return store.list_conversations(workflow_id=workflow_id)


@router.post("/conversations", response_model=Conversation)
def create_conversation(payload: ConversationCreate) -> Conversation:
    workflow = store.get_workflow(payload.workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return store.create_conversation(payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str) -> ConversationDetail:
    conversation = store.get_conversation_with_messages(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str) -> dict[str, bool]:
    deleted = store.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"deleted": True}
