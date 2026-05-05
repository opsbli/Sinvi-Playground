from __future__ import annotations

from .pipeline_schemas import PipelineDefinition, PipelineArtifact
from .pipeline_sequential import StageExecutionInput, StageExecutionResult, StageHandler
from .pipeline_store import PipelineStore
from .pipeline_validation_runner import normalize_validation_commands, run_validation_commands
from .pipeline_workspace_executor import (
    WorkspacePathError,
    materialize_pipeline_files,
    workspace_root_for_run,
)
from .runtime import llm_gateway
from .store import SQLitePlaygroundStore


def _artifact_preview(artifact: PipelineArtifact, *, limit: int = 1600) -> str:
    content = str(artifact.content or "").strip()
    if len(content) > limit:
        return f"{content[:limit]}\n...[truncated]"
    return content


def _stage_prompt(stage_input: StageExecutionInput, upstream_artifacts: list[PipelineArtifact]) -> str:
    story = str(stage_input.input_payload.get("story") or stage_input.input_payload.get("brief") or "").strip()
    story_id = str(stage_input.input_payload.get("story_id") or stage_input.input_payload.get("title") or "").strip()
    artifact_blocks = []
    for artifact in upstream_artifacts:
        artifact_blocks.append(
            f"### {artifact.artifact_type}: {artifact.name}\n"
            f"{_artifact_preview(artifact)}"
        )
    upstream = "\n\n".join(artifact_blocks) if artifact_blocks else "No upstream artifacts yet."
    return (
        "You are executing one stage of an AI Coding pipeline.\n"
        "Do the work for this stage directly and produce a concrete stage report.\n\n"
        f"Pipeline run id: {stage_input.pipeline_run_id}\n"
        f"Stage run id: {stage_input.stage_run_id}\n"
        f"Role: {stage_input.role}\n"
        f"Attempt: {stage_input.attempt}\n"
        f"Story id: {story_id or 'n/a'}\n\n"
        "## Current Story / Input\n"
        f"{story or 'No story content provided.'}\n\n"
        "## Upstream Artifacts\n"
        f"{upstream}\n\n"
        "## Output Requirements\n"
        "- Return only the artifact content for this stage.\n"
        "- Be specific enough that the next pipeline stage can continue without guessing.\n"
        "- If the stage cannot proceed, explain the blocking reason clearly.\n"
    )


def build_agent_stage_handlers(
    *,
    pipeline_store: PipelineStore,
    playground_store: SQLitePlaygroundStore,
    definition: PipelineDefinition,
) -> dict[str, StageHandler]:
    stage_by_role = {stage.role: stage for stage in definition.stages}

    def make_handler(role: str) -> StageHandler:
        def handler(stage_input: StageExecutionInput) -> StageExecutionResult:
            stage_definition = stage_by_role.get(role)
            if stage_definition is None:
                return StageExecutionResult(
                    content="",
                    blocked=True,
                    error_message=f"Stage definition for role '{role}' was not found.",
                )

            agent = playground_store.get_agent(stage_definition.agent_id)
            if agent is None:
                return StageExecutionResult(
                    content="",
                    blocked=True,
                    error_message=f"Stage agent not found: {stage_definition.agent_id}",
                )

            run = pipeline_store.get_pipeline_run(stage_input.pipeline_run_id)
            upstream_artifacts = list(run.artifacts) if run is not None else []
            prompt = _stage_prompt(stage_input, upstream_artifacts)
            try:
                content = llm_gateway.run_agent(agent, prompt)
            except Exception as exc:  # noqa: BLE001 - pipeline must persist runtime failures.
                message = str(exc) or exc.__class__.__name__
                return StageExecutionResult(content="", blocked=True, error_message=message)

            output_payload: dict[str, object] = {
                "role": role,
                "agent_id": agent.id,
                "agent_name": agent.name,
            }
            workspace = workspace_root_for_run(pipeline_store, stage_input.pipeline_run_id)
            if role == "coder":
                try:
                    materialized = materialize_pipeline_files(workspace, content)
                except WorkspacePathError as exc:
                    return StageExecutionResult(content="", blocked=True, error_message=str(exc))
                output_payload["workspace_dir"] = str(materialized.workspace)
                output_payload["generated_files"] = materialized.generated_files
                if materialized.generated_files:
                    pipeline_store.create_pipeline_artifact(
                        stage_input.pipeline_run_id,
                        artifact_type="workspace_manifest",
                        name=f"workspace-attempt-{stage_input.attempt}",
                        content="\n".join(materialized.generated_files),
                        metadata={
                            "role": role,
                            "agent_id": agent.id,
                            "agent_name": agent.name,
                            "workspace_dir": str(materialized.workspace),
                            "generated_files": materialized.generated_files,
                        },
                        stage_run_id=stage_input.stage_run_id,
                    )
            if role == "validator":
                commands = normalize_validation_commands(stage_input.input_payload.get("validation_commands"))
                timeout = int(stage_input.input_payload.get("validation_timeout_seconds") or 30)
                if commands:
                    validation = run_validation_commands(
                        workspace=workspace,
                        commands=commands,
                        timeout_seconds=timeout,
                    )
                    pipeline_store.create_pipeline_artifact(
                        stage_input.pipeline_run_id,
                        artifact_type="validation_commands",
                        name=f"validation-attempt-{stage_input.attempt}",
                        content="\n\n".join(
                            [
                                f"$ {' '.join(record['command'])}\n"
                                f"exit_code={record['exit_code']} timeout={record['timeout']}\n"
                                f"stdout:\n{record['stdout']}\n"
                                f"stderr:\n{record['stderr']}"
                                for record in validation.commands
                            ]
                        ),
                        metadata={
                            "role": role,
                            "agent_id": agent.id,
                            "agent_name": agent.name,
                            "workspace_dir": str(workspace),
                            "passed": validation.passed,
                            "commands": validation.commands,
                        },
                        stage_run_id=stage_input.stage_run_id,
                    )
                    content = (
                        f"{content}\n\n"
                        "## Validation Commands\n"
                        f"passed={validation.passed}\n"
                        + "\n".join(
                            f"- {' '.join(record['command'])}: exit_code={record['exit_code']} timeout={record['timeout']}"
                            for record in validation.commands
                        )
                    )
                    output_payload["validation_commands"] = validation.commands
                    output_payload["passed"] = validation.passed
                else:
                    output_payload["passed"] = True
            return StageExecutionResult(content=content, output_payload=output_payload)

        return handler

    return {role: make_handler(role) for role in stage_by_role}
