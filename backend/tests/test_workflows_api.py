def test_workflows_api_supports_create_and_list(api_client):
    agent_response = api_client.post(
        "/api/agents",
        json={
            "name": "Workflow Agent",
            "description": "Agent for workflow regression tests.",
            "system_prompt": "You help test workflows.",
            "model": "gpt-test",
            "skill_ids": [],
            "builtin_capabilities": ["filesystem"],
        },
    )
    assert agent_response.status_code == 200
    agent = agent_response.json()

    create_response = api_client.post(
        "/api/workflows",
        json={
            "name": "Workflow Regression",
            "type": "single_agent_chat",
            "specialist_agent_ids": [agent["id"]],
            "router_prompt": "Route to the only agent.",
            "finalizer_enabled": True,
        },
    )
    assert create_response.status_code == 200
    workflow = create_response.json()

    list_response = api_client.get("/api/workflows")
    assert list_response.status_code == 200
    assert any(item["id"] == workflow["id"] for item in list_response.json())

