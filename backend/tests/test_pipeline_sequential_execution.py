from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pytest

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.pipeline_store import PipelineStore


def _create_sequential_run(tmp_path: Path):
    store = PipelineStore(tmp_path / "pipeline.db")
    definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding Sequential",
            kind="sequential_pipeline",
            stages=[
                {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1},
                {"name": "Review", "role": "reviewer", "agent_id": "agent_reviewer", "stage_order": 2},
                {"name": "Code", "role": "coder", "agent_id": "agent_coder", "stage_order": 3},
                {"name": "Validate", "role": "validator", "agent_id": "agent_validator", "stage_order": 4},
            ],
        )
    )
    run = store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story": "Build dashboard"}),
    )
    return store, run


def test_sequential_runner_completes_all_stages(tmp_path: Path) -> None:
    from app.pipeline_sequential import StageExecutionResult, run_sequential_pipeline

    store, run = _create_sequential_run(tmp_path)
    calls: list[str] = []

    def handler(stage_input):
        calls.append(stage_input.role)
        return StageExecutionResult(
            content=f"{stage_input.role} output for {stage_input.input_payload['story']}",
            output_payload={"role": stage_input.role},
        )

    result = run_sequential_pipeline(store, run.id, handlers={role: handler for role in ["designer", "reviewer", "coder", "validator"]})
    detail = store.get_pipeline_run(run.id)

    assert result.status == "done"
    assert detail is not None
    assert detail.status == "done"
    assert [stage.status for stage in detail.stage_runs] == ["completed", "completed", "completed", "completed"]
    assert calls == ["designer", "reviewer", "coder", "validator"]
    assert {artifact.artifact_type for artifact in detail.artifacts} >= {
        "design",
        "design_review",
        "implementation",
        "validation_report",
        "trace",
    }
    for stage in detail.stage_runs:
        assert stage.started_at is not None
        assert stage.completed_at is not None
        datetime.fromisoformat(stage.started_at)
        datetime.fromisoformat(stage.completed_at)


def test_sequential_runner_blocks_on_stage_error(tmp_path: Path) -> None:
    from app.pipeline_sequential import StageExecutionResult, run_sequential_pipeline

    store, run = _create_sequential_run(tmp_path)

    def handler(stage_input):
        if stage_input.role == "reviewer":
            raise RuntimeError("review failed")
        return StageExecutionResult(content=f"{stage_input.role} output")

    result = run_sequential_pipeline(store, run.id, handlers={role: handler for role in ["designer", "reviewer", "coder", "validator"]})
    detail = store.get_pipeline_run(run.id)

    assert result.status == "blocked"
    assert detail is not None
    assert detail.status == "blocked"
    assert [stage.status for stage in detail.stage_runs] == ["completed", "blocked", "pending", "pending"]
    assert detail.stage_runs[1].error_message == "review failed"


def test_validator_failure_creates_new_coder_attempt(tmp_path: Path) -> None:
    from app.pipeline_sequential import StageExecutionResult, run_sequential_pipeline

    store, run = _create_sequential_run(tmp_path)

    def handler(stage_input):
        if stage_input.role == "validator":
            return StageExecutionResult(content="Validation failed", output_payload={"passed": False})
        return StageExecutionResult(content=f"{stage_input.role} output")

    result = run_sequential_pipeline(store, run.id, handlers={role: handler for role in ["designer", "reviewer", "coder", "validator"]})
    detail = store.get_pipeline_run(run.id)

    assert result.status == "running"
    assert detail is not None
    assert detail.status == "running"

    coder_runs = [stage for stage in detail.stage_runs if stage.input_payload.get("role") == "coder"]
    assert [stage.attempt for stage in coder_runs] == [0, 1]
    assert coder_runs[-1].status == "pending"
    assert detail.current_stage_id == coder_runs[-1].stage_definition_id


def test_sequential_runner_requires_handlers_for_all_roles(tmp_path: Path) -> None:
    from app.pipeline_sequential import run_sequential_pipeline

    store, run = _create_sequential_run(tmp_path)

    with pytest.raises(ValueError, match="Missing handler"):
        run_sequential_pipeline(store, run.id, handlers={})
