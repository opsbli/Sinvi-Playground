from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .pipeline_schemas import PipelineDefinition, PipelineDefinitionCreate, PipelineRun, PipelineRunCreate
from .pipeline_store import PipelineStore
from .store import store


router = APIRouter()


def _pipeline_store() -> PipelineStore:
    return PipelineStore(store.db_path)


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
