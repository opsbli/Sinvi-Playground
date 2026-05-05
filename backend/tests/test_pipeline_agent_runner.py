from __future__ import annotations

from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.pipeline_sequential import run_sequential_pipeline
from app.pipeline_store import PipelineStore
from app.schemas import AgentDefinitionCreate
from app.store import SQLitePlaygroundStore


def _create_agent(store: SQLitePlaygroundStore, name: str):
    return store.create_agent(
        AgentDefinitionCreate(
            name=name,
            description=f"{name} stage agent.",
            system_prompt=f"You are {name}.",
        )
    )


def test_pipeline_agent_runner_calls_bound_agents_with_upstream_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.pipeline_agent_runner import build_agent_stage_handlers

    playground_store = SQLitePlaygroundStore(tmp_path / "playground.db")
    designer = _create_agent(playground_store, "Design Agent")
    reviewer = _create_agent(playground_store, "Review Agent")
    coder = _create_agent(playground_store, "Code Agent")
    validator = _create_agent(playground_store, "Validate Agent")
    pipeline_store = PipelineStore(playground_store.db_path)
    definition = pipeline_store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding Sequential",
            kind="sequential_pipeline",
            stages=[
                {"name": "Designer", "role": "designer", "agent_id": designer.id, "stage_order": 1},
                {"name": "Reviewer", "role": "reviewer", "agent_id": reviewer.id, "stage_order": 2},
                {"name": "Coder", "role": "coder", "agent_id": coder.id, "stage_order": 3},
                {"name": "Validator", "role": "validator", "agent_id": validator.id, "stage_order": 4},
            ],
        )
    )
    run = pipeline_store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story_id": "US-001", "story": "Build console"}),
    )

    calls: list[tuple[str, str]] = []

    def fake_run_agent(agent, user_input, **_kwargs):
        calls.append((agent.name, user_input))
        return f"{agent.name} completed"

    monkeypatch.setattr("app.pipeline_agent_runner.llm_gateway.run_agent", fake_run_agent)

    result = run_sequential_pipeline(
        pipeline_store,
        run.id,
        handlers=build_agent_stage_handlers(
            pipeline_store=pipeline_store,
            playground_store=playground_store,
            definition=definition,
        ),
    )
    detail = pipeline_store.get_pipeline_run(run.id)

    assert result.status == "done"
    assert [name for name, _prompt in calls] == [
        "Design Agent",
        "Review Agent",
        "Code Agent",
        "Validate Agent",
    ]
    assert "Build console" in calls[0][1]
    assert "design" in calls[1][1]
    assert "Design Agent completed" in calls[1][1]
    assert detail is not None
    design = next(artifact for artifact in detail.artifacts if artifact.artifact_type == "design")
    assert design.metadata["agent_id"] == designer.id
    assert design.metadata["agent_name"] == "Design Agent"


def test_pipeline_agent_runner_blocks_when_stage_agent_is_missing(tmp_path: Path) -> None:
    from app.pipeline_agent_runner import build_agent_stage_handlers

    playground_store = SQLitePlaygroundStore(tmp_path / "playground.db")
    pipeline_store = PipelineStore(playground_store.db_path)
    definition = pipeline_store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding Sequential",
            kind="sequential_pipeline",
            stages=[
                {"name": "Designer", "role": "designer", "agent_id": "agent_missing", "stage_order": 1},
                {"name": "Reviewer", "role": "reviewer", "agent_id": "agent_missing", "stage_order": 2},
                {"name": "Coder", "role": "coder", "agent_id": "agent_missing", "stage_order": 3},
                {"name": "Validator", "role": "validator", "agent_id": "agent_missing", "stage_order": 4},
            ],
        )
    )
    run = pipeline_store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story": "Build console"}),
    )

    result = run_sequential_pipeline(
        pipeline_store,
        run.id,
        handlers=build_agent_stage_handlers(
            pipeline_store=pipeline_store,
            playground_store=playground_store,
            definition=definition,
        ),
    )
    detail = pipeline_store.get_pipeline_run(run.id)

    assert result.status == "blocked"
    assert detail is not None
    assert detail.status == "blocked"
    assert detail.stage_runs[0].status == "blocked"
    assert "not found" in (detail.stage_runs[0].error_message or "")
