def test_agents_api_supports_crud(api_client):
    create_response = api_client.post(
        "/api/agents",
        json={
            "name": "Test Agent",
            "description": "Agent used by regression tests.",
            "system_prompt": "You are a test agent.",
            "model": "gpt-test",
            "skill_ids": [],
            "builtin_capabilities": ["filesystem"],
        },
    )

    assert create_response.status_code == 200
    agent = create_response.json()

    list_response = api_client.get("/api/agents")
    assert list_response.status_code == 200
    assert any(item["id"] == agent["id"] for item in list_response.json())

    update_response = api_client.put(
        f"/api/agents/{agent['id']}",
        json={
            "name": "Updated Agent",
            "description": "Updated regression test agent.",
            "system_prompt": "You are still a test agent.",
            "model": "gpt-test",
            "skill_ids": [],
            "builtin_capabilities": ["filesystem"],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Agent"

    delete_response = api_client.delete(f"/api/agents/{agent['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

