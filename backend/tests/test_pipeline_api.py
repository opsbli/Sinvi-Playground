from __future__ import annotations


def test_pipeline_api_creates_definition_and_run(api_client) -> None:
    definition_response = api_client.post(
        "/api/pipelines",
        json={
            "name": "AI Coding",
            "kind": "sequential_pipeline",
            "description": "Story execution pipeline.",
            "stages": [
                {
                    "name": "Design",
                    "role": "designer",
                    "agent_id": "agent_designer",
                    "stage_order": 1,
                }
            ],
        },
    )
    assert definition_response.status_code == 200
    definition = definition_response.json()

    run_response = api_client.post(
        f"/api/pipelines/{definition['id']}/runs",
        json={"title": "US-001", "input_payload": {"story": "Build layout"}},
    )
    assert run_response.status_code == 200
    assert run_response.json()["current_stage_id"] == definition["stages"][0]["id"]
