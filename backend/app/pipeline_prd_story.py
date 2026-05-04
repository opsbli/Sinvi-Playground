from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from .pipeline_schemas import PipelineArtifact, PipelineRunCreate
from .pipeline_store import PipelineStore


class PrdArtifactCreate(BaseModel):
    brief: str = Field(min_length=1)
    artifact_type: Literal["prd"] = "prd"


class StoryArtifactCreate(BaseModel):
    story_id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1)
    source_prd_artifact_id: str = Field(min_length=1)
    artifact_type: Literal["story"] = "story"


@dataclass(frozen=True)
class PrdStoryGenerationResult:
    pipeline_run_id: str
    prd_artifact: PipelineArtifact
    story_artifacts: list[PipelineArtifact]


def generate_prd_from_brief(brief: str) -> str:
    cleaned = " ".join(brief.split())
    return (
        "# PRD\n\n"
        "## Brief\n"
        f"{cleaned}\n\n"
        "## Goals\n"
        f"- Deliver: {cleaned}\n\n"
        "## User Stories Seed\n"
        f"- Build {cleaned}\n"
        "- Validate the implementation against acceptance criteria\n\n"
        "## Non-Goals\n"
        "- Do not execute downstream implementation agents in this stage.\n\n"
        "## Acceptance Criteria\n"
        "- PRD artifact is persisted.\n"
        "- Story artifacts can seed sequential pipeline runs.\n"
    )


def _title_from_bullet(text: str) -> str:
    cleaned = re.sub(r"^(build|create|implement|validate)\s+", "", text.strip(), flags=re.IGNORECASE)
    return cleaned[:120].strip(" .") or "Pipeline story"


def _section_lines(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    captured: list[str] = []
    in_section = False
    target = f"## {heading}".casefold()
    for line in lines:
        normalized = line.strip().casefold()
        if normalized == target:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            captured.append(line)
    return captured


def split_prd_into_stories(prd_content: str, *, source_prd_artifact_id: str) -> list[StoryArtifactCreate]:
    story_seed_lines = _section_lines(prd_content, "User Stories Seed")
    bullets = [line[2:].strip() for line in story_seed_lines if line.startswith("- ") and line[2:].strip()]
    if not bullets:
        bullets = ["Implement the PRD scope"]

    stories: list[StoryArtifactCreate] = []
    seen_titles: set[str] = set()
    for index, bullet in enumerate(bullets, start=1):
        title = _title_from_bullet(bullet)
        if title in seen_titles:
            continue
        seen_titles.add(title)
        story_id = f"US-{index:03d}"
        content = (
            f"# Story: {story_id} - {title}\n\n"
            "## User Value\n"
            f"As a user, I need {title}.\n\n"
            "## Source Requirement\n"
            f"{bullet}\n\n"
            "## Acceptance Criteria\n"
            f"- {bullet}\n"
        )
        stories.append(
            StoryArtifactCreate(
                story_id=story_id,
                title=title,
                content=content,
                source_prd_artifact_id=source_prd_artifact_id,
            )
        )
    return stories


def run_prd_story_generation(store: PipelineStore, pipeline_id: str, *, brief: str) -> PrdStoryGenerationResult:
    run = store.create_pipeline_run(
        pipeline_id,
        PipelineRunCreate(title="PRD Story Generation", input_payload={"brief": brief}),
    )
    prd_content = generate_prd_from_brief(brief)
    prd_artifact = store.create_pipeline_artifact(
        run.id,
        artifact_type="prd",
        name="PRD",
        content=prd_content,
        metadata={"brief": brief},
    )
    story_payloads = split_prd_into_stories(prd_content, source_prd_artifact_id=prd_artifact.id)
    story_artifacts = [
        store.create_pipeline_artifact(
            run.id,
            artifact_type="story",
            name=story.story_id,
            content=story.content,
            metadata={
                "story_id": story.story_id,
                "title": story.title,
                "source_prd_artifact_id": story.source_prd_artifact_id,
            },
        )
        for story in story_payloads
    ]
    return PrdStoryGenerationResult(
        pipeline_run_id=run.id,
        prd_artifact=prd_artifact,
        story_artifacts=story_artifacts,
    )
