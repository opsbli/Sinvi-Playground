from __future__ import annotations

import sys


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


def test_pipeline_api_rejects_duplicate_stage_order(api_client) -> None:
    response = api_client.post(
        "/api/pipelines",
        json={
            "name": "AI Coding",
            "kind": "sequential_pipeline",
            "stages": [
                {
                    "name": "Design",
                    "role": "designer",
                    "agent_id": "agent_designer",
                    "stage_order": 1,
                },
                {
                    "name": "Review",
                    "role": "reviewer",
                    "agent_id": "agent_reviewer",
                    "stage_order": 1,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_pipeline_api_bootstraps_ai_coding_definitions_idempotently(api_client) -> None:
    first_response = api_client.post("/api/pipelines/ai-coding/bootstrap")
    second_response = api_client.post("/api/pipelines/ai-coding/bootstrap")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first = first_response.json()
    second = second_response.json()
    assert first["prd_story_definition"]["id"] == second["prd_story_definition"]["id"]
    assert first["sequential_definition"]["id"] == second["sequential_definition"]["id"]
    assert [stage["role"] for stage in first["prd_story_definition"]["stages"]] == [
        "prd_writer",
        "story_splitter",
    ]
    assert [stage["role"] for stage in first["sequential_definition"]["stages"]] == [
        "designer",
        "reviewer",
        "coder",
        "validator",
    ]


def test_pipeline_api_generates_prd_and_story_artifacts(api_client) -> None:
    bootstrap = api_client.post("/api/pipelines/ai-coding/bootstrap").json()

    response = api_client.post(
        "/api/pipelines/prd-story-generation",
        json={
            "pipeline_id": bootstrap["prd_story_definition"]["id"],
            "brief": "Build a pipeline console for PRD and story execution.",
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "pending"
    assert {artifact["artifact_type"] for artifact in run["artifacts"]} >= {"prd", "story"}


def test_pipeline_api_executes_sequential_story_run(api_client) -> None:
    bootstrap = api_client.post("/api/pipelines/ai-coding/bootstrap").json()
    run_response = api_client.post(
        f"/api/pipelines/{bootstrap['sequential_definition']['id']}/runs",
        json={
            "title": "US-001",
            "input_payload": {
                "story_id": "US-001",
                "story": "# Story\n\nBuild the pipeline console.",
                "validation_commands": [[sys.executable, "-c", "print('api validation ok')"]],
            },
        },
    )
    run = run_response.json()

    response = api_client.post(f"/api/pipelines/runs/{run['id']}/execute-sequential")

    assert response.status_code == 200
    detail = response.json()
    assert detail["status"] == "done"
    assert [stage["status"] for stage in detail["stage_runs"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert {artifact["artifact_type"] for artifact in detail["artifacts"]} >= {
        "design",
        "design_review",
        "implementation",
        "validation_report",
        "validation_commands",
    }
    design_artifact = next(artifact for artifact in detail["artifacts"] if artifact["artifact_type"] == "design")
    assert design_artifact["metadata"]["agent_id"]
    assert design_artifact["metadata"]["agent_name"] == "AI Coding Designer"
    validation_artifact = next(artifact for artifact in detail["artifacts"] if artifact["artifact_type"] == "validation_commands")
    assert validation_artifact["metadata"]["passed"] is True
    assert validation_artifact["metadata"]["commands"][0]["exit_code"] == 0
