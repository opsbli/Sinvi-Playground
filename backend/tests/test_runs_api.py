def test_runs_api_returns_404_for_missing_workflow(api_client):
    response = api_client.post(
        "/api/runs",
        json={
            "workflow_id": "missing-workflow",
            "user_input": "hello",
            "conversation_id": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found."

