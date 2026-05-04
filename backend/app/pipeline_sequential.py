from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal

from .pipeline_schemas import PipelineRun, PipelineStageRun
from .pipeline_store import PipelineStore


AI_CODING_ROLES = ("designer", "reviewer", "coder", "validator")
ARTIFACT_TYPE_BY_ROLE = {
    "designer": "design",
    "reviewer": "design_review",
    "coder": "implementation",
    "validator": "validation_report",
}


@dataclass(frozen=True)
class StageExecutionInput:
    pipeline_run_id: str
    stage_run_id: str
    stage_definition_id: str
    role: str
    attempt: int
    input_payload: dict[str, object]
    upstream_artifacts: list[dict[str, object]] = field(default_factory=list)


@dataclass(frozen=True)
class StageExecutionResult:
    content: str
    output_payload: dict[str, object] = field(default_factory=dict)
    blocked: bool = False
    error_message: str | None = None


@dataclass(frozen=True)
class SequentialPipelineResult:
    pipeline_run_id: str
    status: Literal["done", "running", "blocked"]


StageHandler = Callable[[StageExecutionInput], StageExecutionResult]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage_role(run: PipelineRun, stage_run: PipelineStageRun) -> str:
    for artifact_stage in run.stage_runs:
        if artifact_stage.id == stage_run.id:
            break
    # Stage definitions are not embedded in stage runs, so infer from initial input
    role = str(stage_run.input_payload.get("role") or "").strip()
    if role:
        return role
    raise ValueError("Stage run input_payload must include role.")


def _definition_role(run: PipelineRun, stage_run: PipelineStageRun) -> str:
    role = str(stage_run.input_payload.get("role") or "").strip()
    if role:
        return role
    # Initial stage runs are created before role is copied into input_payload. Use artifact-free
    # ordering expected by the AI Coding pipeline roles.
    ordered_stage_ids = []
    seen = set()
    for item in run.stage_runs:
        if item.stage_definition_id not in seen:
            seen.add(item.stage_definition_id)
            ordered_stage_ids.append(item.stage_definition_id)
    try:
        return AI_CODING_ROLES[ordered_stage_ids.index(stage_run.stage_definition_id)]
    except (ValueError, IndexError) as exc:
        raise ValueError("Unsupported sequential pipeline stage layout.") from exc


def _stage_input_payload(run: PipelineRun, role: str, attempt: int) -> dict[str, object]:
    payload: dict[str, object] = dict(run.input_payload)
    payload["role"] = role
    payload["attempt"] = attempt
    return payload


def _trace(store: PipelineStore, run_id: str, event: str, payload: dict[str, object]) -> None:
    store.create_pipeline_artifact(
        run_id,
        artifact_type="trace",
        name=event,
        content=event,
        metadata=payload,
    )


def _pending_stage_runs(run: PipelineRun) -> list[PipelineStageRun]:
    return [stage for stage in run.stage_runs if stage.status == "pending"]


def _latest_attempt(run: PipelineRun, stage_definition_id: str) -> int:
    attempts = [stage.attempt for stage in run.stage_runs if stage.stage_definition_id == stage_definition_id]
    return max(attempts) if attempts else 0


def _validate_handlers(handlers: dict[str, StageHandler]) -> None:
    missing = [role for role in AI_CODING_ROLES if role not in handlers]
    if missing:
        raise ValueError(f"Missing handler for role(s): {', '.join(missing)}")


def run_sequential_pipeline(
    store: PipelineStore,
    pipeline_run_id: str,
    *,
    handlers: dict[str, StageHandler],
) -> SequentialPipelineResult:
    _validate_handlers(handlers)
    run = store.get_pipeline_run(pipeline_run_id)
    if run is None:
        raise ValueError("Pipeline run not found.")

    store.update_pipeline_run_status(run.id, status="running", current_stage_id=run.current_stage_id)
    run = store.get_pipeline_run(run.id)
    if run is None:
        raise ValueError("Pipeline run not found.")

    for stage_run in _pending_stage_runs(run):
        role = _definition_role(run, stage_run)
        attempt = stage_run.attempt
        input_payload = _stage_input_payload(run, role, attempt)
        started_at = _utc_now_iso()
        store.update_stage_run(
            stage_run.id,
            status="running",
            input_payload=input_payload,
            started_at=started_at,
        )
        store.update_pipeline_run_status(run.id, status="running", current_stage_id=stage_run.stage_definition_id)
        _trace(store, run.id, "stage_started", {"stage_run_id": stage_run.id, "role": role, "attempt": attempt})

        stage_input = StageExecutionInput(
            pipeline_run_id=run.id,
            stage_run_id=stage_run.id,
            stage_definition_id=stage_run.stage_definition_id,
            role=role,
            attempt=attempt,
            input_payload=input_payload,
            upstream_artifacts=[
                {"id": artifact.id, "artifact_type": artifact.artifact_type, "name": artifact.name}
                for artifact in run.artifacts
            ],
        )
        try:
            output = handlers[role](stage_input)
        except Exception as exc:  # noqa: BLE001 - runner must persist handler failures.
            message = str(exc) or exc.__class__.__name__
            store.update_stage_run(stage_run.id, status="blocked", error_message=message, completed_at=_utc_now_iso())
            store.update_pipeline_run_status(run.id, status="blocked", current_stage_id=stage_run.stage_definition_id)
            _trace(store, run.id, "stage_blocked", {"stage_run_id": stage_run.id, "role": role, "error": message})
            return SequentialPipelineResult(pipeline_run_id=run.id, status="blocked")

        if output.blocked:
            message = output.error_message or "Stage blocked."
            store.update_stage_run(stage_run.id, status="blocked", error_message=message, completed_at=_utc_now_iso())
            store.update_pipeline_run_status(run.id, status="blocked", current_stage_id=stage_run.stage_definition_id)
            _trace(store, run.id, "stage_blocked", {"stage_run_id": stage_run.id, "role": role, "error": message})
            return SequentialPipelineResult(pipeline_run_id=run.id, status="blocked")

        if role == "validator" and output.output_payload.get("passed") is False:
            store.update_stage_run(
                stage_run.id,
                status="failed",
                output_payload=output.output_payload,
                completed_at=_utc_now_iso(),
            )
            store.create_pipeline_artifact(
                run.id,
                artifact_type=ARTIFACT_TYPE_BY_ROLE[role],
                name=f"{role}-attempt-{attempt}",
                content=output.content,
                metadata={"role": role, "attempt": attempt, "passed": False},
                stage_run_id=stage_run.id,
            )
            coder_stage = next(item for item in run.stage_runs if _definition_role(run, item) == "coder")
            next_attempt = _latest_attempt(run, coder_stage.stage_definition_id) + 1
            retry = store.create_stage_run(
                run.id,
                coder_stage.stage_definition_id,
                attempt=next_attempt,
                input_payload=_stage_input_payload(run, "coder", next_attempt),
            )
            store.update_pipeline_run_status(run.id, status="running", current_stage_id=retry.stage_definition_id)
            _trace(
                store,
                run.id,
                "validator_retry",
                {"validator_stage_run_id": stage_run.id, "coder_stage_run_id": retry.id, "attempt": next_attempt},
            )
            return SequentialPipelineResult(pipeline_run_id=run.id, status="running")

        store.update_stage_run(
            stage_run.id,
            status="completed",
            output_payload=output.output_payload,
            completed_at=_utc_now_iso(),
        )
        store.create_pipeline_artifact(
            run.id,
            artifact_type=ARTIFACT_TYPE_BY_ROLE[role],
            name=f"{role}-attempt-{attempt}",
            content=output.content,
            metadata={"role": role, "attempt": attempt},
            stage_run_id=stage_run.id,
        )
        _trace(store, run.id, "stage_completed", {"stage_run_id": stage_run.id, "role": role, "attempt": attempt})
        run = store.get_pipeline_run(run.id)
        if run is None:
            raise ValueError("Pipeline run not found.")

    store.update_pipeline_run_status(run.id, status="done", current_stage_id=None)
    _trace(store, run.id, "pipeline_done", {"pipeline_run_id": run.id})
    return SequentialPipelineResult(pipeline_run_id=run.id, status="done")
