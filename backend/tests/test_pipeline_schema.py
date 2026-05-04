from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate


def test_pipeline_definition_create_defaults() -> None:
    payload = PipelineDefinitionCreate(
        name="AI Coding",
        kind="sequential_pipeline",
        description="Story execution pipeline.",
        stages=[
            {
                "name": "Design",
                "role": "designer",
                "agent_id": "agent_designer",
                "stage_order": 1,
            }
        ],
    )

    assert payload.stages[0].retry_limit == 1


def test_pipeline_run_create_accepts_input_payload() -> None:
    payload = PipelineRunCreate(
        title="US-001",
        input_payload={"story": "Build layout"},
    )

    assert payload.input_payload["story"] == "Build layout"


def test_pipeline_definition_rejects_duplicate_stage_order() -> None:
    with pytest.raises(ValidationError):
        PipelineDefinitionCreate(
            name="AI Coding",
            kind="sequential_pipeline",
            stages=[
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
        )
