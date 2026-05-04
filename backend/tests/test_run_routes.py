from __future__ import annotations

import importlib
from types import SimpleNamespace

from app.schemas import Conversation, TraceEvent, WorkflowDefinition, WorkflowRunRequest


def _load_module():
    return importlib.import_module("app.routes_runs")


class FakeStore:
    def __init__(self) -> None:
        self.workflow = WorkflowDefinition(
            id="workflow-1",
            name="Workflow",
            type="single_agent_chat",
            specialist_agent_ids=["agent-1"],
            router_prompt="Route well.",
            finalizer_enabled=True,
        )
        self.conversations: dict[str, Conversation] = {}
        self.messages: list[dict[str, str | None]] = []
        self.created_titles: list[tuple[str, str]] = []
        self.recent_messages = [
            SimpleNamespace(role="user", content="previous question"),
            SimpleNamespace(role="assistant", content="previous answer"),
        ]

    def get_workflow(self, workflow_id: str):
        if workflow_id == self.workflow.id:
            return self.workflow
        return None

    def create_conversation(self, payload):
        conversation = Conversation(
            id="conversation-1",
            workflow_id=payload.workflow_id,
            title=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        self.conversations[conversation.id] = conversation
        return conversation

    def create_message(self, conversation_id: str, role: str, content: str, agent_name=None):
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "agent_name": agent_name,
            }
        )

    def get_conversation(self, conversation_id: str):
        return self.conversations[conversation_id]

    def update_conversation_title(self, conversation_id: str, title: str):
        self.created_titles.append((conversation_id, title))
        conversation = self.conversations[conversation_id]
        self.conversations[conversation_id] = conversation.model_copy(update={"title": title})

    def get_recent_messages(self, conversation_id: str, limit: int = 2):  # noqa: ARG002
        return self.recent_messages


def test_dispatch_run_uses_recent_history_and_workflow_type(monkeypatch):
    module = _load_module()
    fake_store = FakeStore()
    monkeypatch.setattr(module, "store", fake_store)

    captured = {}

    def fake_run_single_agent_chat(store, workflow, user_input, history, on_event=None):  # noqa: ANN001
        captured["store"] = store
        captured["workflow_id"] = workflow.id
        captured["user_input"] = user_input
        captured["history"] = history
        captured["on_event"] = on_event
        return SimpleNamespace(
            assistant_message="assistant reply",
            artifacts=SimpleNamespace(route_agent_name="agent-1"),
            model_dump=lambda: {
                "workflow_id": workflow.id,
                "user_input": user_input,
                "assistant_message": "assistant reply",
                "trace": [],
                "graph": {"nodes": [], "edges": []},
                "artifacts": {"route_agent_name": "agent-1"},
                "conversation_id": None,
            },
        )

    monkeypatch.setattr(module, "run_single_agent_chat", fake_run_single_agent_chat)

    result = module._dispatch_run(
        fake_store.workflow,
        "hello world",
        conversation_id="conversation-1",
    )

    assert result.assistant_message == "assistant reply"
    assert captured["store"] is fake_store
    assert captured["workflow_id"] == "workflow-1"
    assert captured["user_input"] == "hello world"
    assert captured["history"] == [
        {"role": "user", "content": "previous question"},
        {"role": "assistant", "content": "previous answer"},
    ]


def test_run_workflow_persists_messages_and_title(monkeypatch):
    module = _load_module()
    fake_store = FakeStore()
    monkeypatch.setattr(module, "store", fake_store)

    def fake_dispatch_run(workflow, user_input, conversation_id=None, on_event=None):  # noqa: ANN001
        return SimpleNamespace(
            assistant_message="assistant reply",
            artifacts=SimpleNamespace(route_agent_name="agent-1"),
            model_dump=lambda: {
                "workflow_id": workflow.id,
                "user_input": user_input,
                "assistant_message": "assistant reply",
                "trace": [],
                "graph": {"nodes": [], "edges": []},
                "artifacts": {"route_agent_name": "agent-1"},
                "conversation_id": conversation_id,
            },
            conversation_id=conversation_id,
        )

    monkeypatch.setattr(module, "_dispatch_run", fake_dispatch_run)

    result = module.run_workflow(
        WorkflowRunRequest(
            workflow_id="workflow-1",
            user_input="hello world",
            conversation_id=None,
        )
    )

    assert result.conversation_id == "conversation-1"
    assert fake_store.messages == [
        {
            "conversation_id": "conversation-1",
            "role": "user",
            "content": "hello world",
            "agent_name": None,
        },
        {
            "conversation_id": "conversation-1",
            "role": "assistant",
            "content": "assistant reply",
            "agent_name": "agent-1",
        },
    ]
    assert fake_store.created_titles == [("conversation-1", "hello world")]
