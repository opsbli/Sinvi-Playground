from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .runtime import llm_gateway
from .schemas import (
    SkillDefinition,
    SkillDefinitionCreate,
    SkillInstallResponse,
    SkillSyncRequest,
    SkillSyncResponse,
)
from .skillhub_client import skillhub_client
from .store import store


router = APIRouter()


@router.get("/skills", response_model=list[SkillDefinition])
def list_skills() -> list[SkillDefinition]:
    skills = store.list_skills()
    for skill in skills:
        skill.runtime_preflight = llm_gateway.build_skill_preflight(skill)
    return skills


@router.post("/skills", response_model=SkillDefinition)
def create_skill(payload: SkillDefinitionCreate) -> SkillDefinition:
    return store.create_skill(payload)


@router.post("/skills/{skill_id}/install", response_model=SkillInstallResponse)
def install_skill(skill_id: str) -> SkillInstallResponse:
    skill = store.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found.")

    provider = str(skill.source_provider or "").strip().lower()
    source_skill_id = str(skill.source_skill_id or "").strip() or None

    if provider == "skillhub":
        if not source_skill_id:
            raise HTTPException(status_code=400, detail="SkillHub skill missing source_skill_id.")
        try:
            remote = skillhub_client.fetch_skill_package(source_skill_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

        package_files = remote.package_files or {}
        if not package_files:
            raise HTTPException(
                status_code=409,
                detail=(
                    "SkillHub returned metadata only (no package files). "
                    "This skill cannot be truly installed yet."
                ),
            )

        installed = store.install_skill_package(
            skill_id=skill.id,
            name=remote.name or skill.name,
            description=remote.description or skill.description,
            instruction=remote.instruction or skill.instruction,
            tool=remote.tool,
            package_files=package_files,
        )
        if installed is None:
            raise HTTPException(status_code=404, detail="Skill not found.")

        return SkillInstallResponse(
            skill_id=installed.id,
            skill_name=installed.name,
            source_provider=installed.source_provider,
            source_skill_id=installed.source_skill_id,
            downloaded_files=len(package_files),
            tool_enabled=bool(installed.tool),
            message=f"Skill package downloaded: {len(package_files)} files.",
        )

    return SkillInstallResponse(
        skill_id=skill.id,
        skill_name=skill.name,
        source_provider=skill.source_provider,
        source_skill_id=skill.source_skill_id,
        downloaded_files=0,
        tool_enabled=bool(skill.tool),
        message="Local skill is ready.",
    )


@router.post("/skills/sync", response_model=SkillSyncResponse)
def sync_skills(payload: SkillSyncRequest) -> SkillSyncResponse:
    if payload.provider != "skillhub":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {payload.provider}")

    query = (payload.query or "").strip() or "search"

    try:
        remote_skills = skillhub_client.fetch_skills(query=query, limit=payload.limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    imported, updated = store.upsert_marketplace_skills(
        source_provider="skillhub",
        skills=[
            {
                "source_skill_id": skill.source_skill_id,
                "name": skill.name,
                "description": skill.description,
                "instruction": skill.instruction,
                "tool": skill.tool,
                "package_files": skill.package_files,
            }
            for skill in remote_skills
        ],
    )

    return SkillSyncResponse(
        provider="skillhub",
        query=query,
        fetched=len(remote_skills),
        imported=imported,
        updated=updated,
    )
