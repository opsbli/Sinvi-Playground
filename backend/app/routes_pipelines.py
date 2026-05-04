from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .pipeline_prd_story import run_prd_story_generation
from .pipeline_schemas import PipelineDefinition, PipelineDefinitionCreate, PipelineRun, PipelineRunCreate
from .pipeline_sequential import StageExecutionResult, run_sequential_pipeline
from .pipeline_store import PipelineStore
from .schemas import AgentDefinitionCreate
from .seeds.pipeline_prd_story_agents import seed_prd_story_agents
from .store import store


router = APIRouter()


class AiCodingBootstrapResponse(BaseModel):
    prd_story_definition: PipelineDefinition
    sequential_definition: PipelineDefinition


class PrdStoryGenerationRequest(BaseModel):
    brief: str = Field(min_length=1)
    pipeline_id: str | None = None


def _pipeline_store() -> PipelineStore:
    return PipelineStore(store.db_path)


def _find_pipeline_definition(
    pipeline_store: PipelineStore,
    *,
    name: str,
    kind: str,
) -> PipelineDefinition | None:
    for definition in pipeline_store.list_pipeline_definitions():
        if definition.name == name and definition.kind == kind:
            return definition
    return None


def _find_agent_by_name(name: str):
    for agent in store.list_agents():
        if agent.name == name:
            return agent
    return None


def _ensure_execution_agents() -> dict[str, str]:
    prompts_by_role = {
        "designer": "You are the Designer stage in the AI Coding pipeline. Produce implementation-ready design notes for the current story.",
        "reviewer": "You are the Reviewer stage in the AI Coding pipeline. Review upstream design artifacts and call out risks before coding.",
        "coder": "You are the Coder stage in the AI Coding pipeline. Convert the approved story and design into an implementation report.",
        "validator": "You are the Validator stage in the AI Coding pipeline. Validate the implementation against story acceptance criteria.",
    }
    agent_ids_by_role: dict[str, str] = {}
    for role, prompt in prompts_by_role.items():
        name = f"AI Coding {role.replace('_', ' ').title()}"
        existing = _find_agent_by_name(name)
        if existing is None:
            existing = store.create_agent(
                AgentDefinitionCreate(
                    name=name,
                    description=f"Built-in {role} agent for AI Coding sequential pipeline.",
                    system_prompt=prompt,
                    builtin_capabilities=["filesystem"],
                )
            )
        agent_ids_by_role[role] = existing.id
    return agent_ids_by_role


def _ensure_pipeline_definitions() -> AiCodingBootstrapResponse:
    pipeline_store = _pipeline_store()
    prd_story_agents = seed_prd_story_agents(store)
    execution_agents = _ensure_execution_agents()

    prd_story_definition = _find_pipeline_definition(
        pipeline_store,
        name="PRD Story Generation",
        kind="prd_story_generation",
    )
    if prd_story_definition is None:
        prd_story_definition = pipeline_store.create_pipeline_definition(
            PipelineDefinitionCreate(
                name="PRD Story Generation",
                kind="prd_story_generation",
                description="Generate a PRD and split it into executable stories.",
                stages=[
                    {
                        "name": "PRD Writer",
                        "role": "prd_writer",
                        "agent_id": prd_story_agents.agent_ids_by_role["prd_writer"],
                        "stage_order": 1,
                    },
                    {
                        "name": "Story Splitter",
                        "role": "story_splitter",
                        "agent_id": prd_story_agents.agent_ids_by_role["story_splitter"],
                        "stage_order": 2,
                    },
                ],
            )
        )

    sequential_definition = _find_pipeline_definition(
        pipeline_store,
        name="AI Coding Sequential",
        kind="sequential_pipeline",
    )
    if sequential_definition is None:
        sequential_definition = pipeline_store.create_pipeline_definition(
            PipelineDefinitionCreate(
                name="AI Coding Sequential",
                kind="sequential_pipeline",
                description="Execute one story through designer, reviewer, coder, and validator stages.",
                stages=[
                    {
                        "name": "Designer",
                        "role": "designer",
                        "agent_id": execution_agents["designer"],
                        "stage_order": 1,
                    },
                    {
                        "name": "Reviewer",
                        "role": "reviewer",
                        "agent_id": execution_agents["reviewer"],
                        "stage_order": 2,
                    },
                    {
                        "name": "Coder",
                        "role": "coder",
                        "agent_id": execution_agents["coder"],
                        "stage_order": 3,
                    },
                    {
                        "name": "Validator",
                        "role": "validator",
                        "agent_id": execution_agents["validator"],
                        "stage_order": 4,
                    },
                ],
            )
        )

    return AiCodingBootstrapResponse(
        prd_story_definition=prd_story_definition,
        sequential_definition=sequential_definition,
    )


def _stage_handler(stage_input) -> StageExecutionResult:
    story = str(stage_input.input_payload.get("story") or stage_input.input_payload.get("brief") or "").strip()
    story_id = str(stage_input.input_payload.get("story_id") or "story").strip()
    upstream = ", ".join(str(item.get("artifact_type")) for item in stage_input.upstream_artifacts) or "none"
    content = (
        f"# {stage_input.role.title()} Report\n\n"
        f"## Story\n{story_id}\n\n"
        f"## Input\n{story or 'No story content provided.'}\n\n"
        f"## Upstream Artifacts\n{upstream}\n\n"
        "## Result\n"
        f"{stage_input.role} stage completed for this pipeline run.\n"
    )
    output_payload = {"role": stage_input.role, "story_id": story_id}
    if stage_input.role == "validator":
        output_payload["passed"] = True
    return StageExecutionResult(content=content, output_payload=output_payload)


@router.post("/pipelines/ai-coding/bootstrap", response_model=AiCodingBootstrapResponse)
def bootstrap_ai_coding_pipeline() -> AiCodingBootstrapResponse:
    return _ensure_pipeline_definitions()


@router.post("/pipelines/prd-story-generation", response_model=PipelineRun)
def create_prd_story_generation_run(payload: PrdStoryGenerationRequest) -> PipelineRun:
    bootstrap = _ensure_pipeline_definitions()
    pipeline_id = payload.pipeline_id or bootstrap.prd_story_definition.id
    result = run_prd_story_generation(_pipeline_store(), pipeline_id, brief=payload.brief)
    run = _pipeline_store().get_pipeline_run(result.pipeline_run_id)
    if run is None:
        raise HTTPException(status_code=500, detail="Pipeline run was not persisted.")
    return run


@router.post("/pipelines/runs/{run_id}/execute-sequential", response_model=PipelineRun)
def execute_sequential_pipeline_run(run_id: str) -> PipelineRun:
    pipeline_store = _pipeline_store()
    run = pipeline_store.get_pipeline_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    definition = pipeline_store.get_pipeline_definition(run.pipeline_id)
    if definition is None or definition.kind != "sequential_pipeline":
        raise HTTPException(status_code=400, detail="Pipeline run is not sequential.")
    run_sequential_pipeline(
        pipeline_store,
        run_id,
        handlers={
            "designer": _stage_handler,
            "reviewer": _stage_handler,
            "coder": _stage_handler,
            "validator": _stage_handler,
        },
    )
    detail = pipeline_store.get_pipeline_run(run_id)
    if detail is None:
        raise HTTPException(status_code=500, detail="Pipeline run was not persisted.")
    return detail


@router.get("/pipelines", response_model=list[PipelineDefinition])
def list_pipeline_definitions() -> list[PipelineDefinition]:
    return _pipeline_store().list_pipeline_definitions()


@router.post("/pipelines", response_model=PipelineDefinition)
def create_pipeline_definition(payload: PipelineDefinitionCreate) -> PipelineDefinition:
    return _pipeline_store().create_pipeline_definition(payload)


@router.get("/pipelines/runs/{run_id}", response_model=PipelineRun)
def get_pipeline_run(run_id: str) -> PipelineRun:
    run = _pipeline_store().get_pipeline_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    return run


@router.get("/pipelines/{pipeline_id}", response_model=PipelineDefinition)
def get_pipeline_definition(pipeline_id: str) -> PipelineDefinition:
    definition = _pipeline_store().get_pipeline_definition(pipeline_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Pipeline definition not found.")
    return definition


@router.post("/pipelines/{pipeline_id}/runs", response_model=PipelineRun)
def create_pipeline_run(pipeline_id: str, payload: PipelineRunCreate) -> PipelineRun:
    try:
        return _pipeline_store().create_pipeline_run(pipeline_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Pipeline definition not found.") from exc
