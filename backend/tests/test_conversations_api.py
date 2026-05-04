def test_conversations_api_supports_crud(api_client):
    agent_response = api_client.post(
        "/api/agents",
        json={
            "name": "Conversation Agent",
            "description": "Agent for conversation regression tests.",
            "system_prompt": "You help test conversations.",
            "model": "gpt-test",
            "skill_ids": [],
            "builtin_capabilities": ["filesystem"],
        },
    )
    assert agent_response.status_code == 200
    agent = agent_response.json()

    workflow_response = api_client.post(
        "/api/workflows",
        json={
            "name": "Conversation Workflow",
            "type": "single_agent_chat",
            "specialist_agent_ids": [agent["id"]],
            "router_prompt": "Route to the single agent.",
            "finalizer_enabled": True,
        },
    )
    assert workflow_response.status_code == 200
    workflow = workflow_response.json()

    create_response = api_client.post("/api/conversations", json={"workflow_id": workflow["id"]})
    assert create_response.status_code == 200
    conversation = create_response.json()

    list_response = api_client.get("/api/conversations", params={"workflow_id": workflow["id"]})
    assert list_response.status_code == 200
    assert any(item["id"] == conversation["id"] for item in list_response.json())

    detail_response = api_client.get(f"/api/conversations/{conversation['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["messages"] == []

    delete_response = api_client.delete(f"/api/conversations/{conversation['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

