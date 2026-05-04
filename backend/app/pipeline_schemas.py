from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


PipelineRunStatus = Literal["pending", "running", "done", "blocked", "failed"]
PipelineStageRunStatus = Literal["pending", "running", "completed", "failed", "blocked"]


class PipelineStageDefinitionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=80)
    agent_id: str = Field(min_length=1, max_length=120)
    stage_order: int = Field(ge=1)
    retry_limit: int = Field(default=1, ge=0)


class PipelineDefinitionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    stages: list[PipelineStageDefinitionCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_stage_order(self) -> "PipelineDefinitionCreate":
        stage_orders = [stage.stage_order for stage in self.stages]
        if len(stage_orders) != len(set(stage_orders)):
            raise ValueError("stage_order values must be unique within a pipeline definition.")
        return self


class PipelineStageDefinition(PipelineStageDefinitionCreate):
    id: str
    pipeline_id: str


class PipelineDefinition(BaseModel):
    id: str
    name: str
    kind: str
    description: str | None = None
    stages: list[PipelineStageDefinition] = Field(default_factory=list)
    created_at: str
    updated_at: str


class PipelineRunCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    input_payload: dict[str, Any] = Field(default_factory=dict)


class PipelineStageRun(BaseModel):
    id: str
    pipeline_run_id: str
    stage_definition_id: str
    status: PipelineStageRunStatus = "pending"
    attempt: int = 0
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class PipelineArtifact(BaseModel):
    id: str
    pipeline_run_id: str
    stage_run_id: str | None = None
    artifact_type: str
    name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class PipelineRun(BaseModel):
    id: str
    pipeline_id: str
    title: str
    source_prd_id: str | None = None
    status: PipelineRunStatus = "pending"
    current_stage_id: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    stage_runs: list[PipelineStageRun] = Field(default_factory=list)
    artifacts: list[PipelineArtifact] = Field(default_factory=list)
    created_at: str
    updated_at: str
