from __future__ import annotations

from fastapi import APIRouter

from .routes_agents import router as agents_router
from .routes_conversations import router as conversations_router
from .routes_runs import router as runs_router
from .routes_skills import router as skills_router
from .routes_workflows import router as workflows_router
from .runtime import llm_gateway
from .schemas import AppSettings
from .settings_bridge import apply_structured_settings, normalize_structured_settings, settings
from .store import store


router = APIRouter(prefix="/api")
router.include_router(agents_router)
router.include_router(skills_router)
router.include_router(conversations_router)
router.include_router(workflows_router)
router.include_router(runs_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/settings", response_model=AppSettings)
def get_app_settings() -> AppSettings:
    structured = normalize_structured_settings(store.get_app_settings_payload())
    return AppSettings(
        model_profiles=structured["model_profiles"],  # type: ignore[arg-type]
        active_model_profile_id=str(structured["active_model_profile_id"] or "") or None,
        env_vars=structured["env_vars"],  # type: ignore[arg-type]
        env_path=settings.APP_ENV_PATH,
    )


@router.put("/settings", response_model=AppSettings)
def update_app_settings(payload: AppSettings) -> AppSettings:
    previous = store.get_app_settings_payload()
    current = normalize_structured_settings(payload.model_dump())
    store.save_app_settings_payload(current)
    apply_structured_settings(previous, current)
    llm_gateway.refresh_client()
    structured = normalize_structured_settings(store.get_app_settings_payload())
    return AppSettings(
        model_profiles=structured["model_profiles"],  # type: ignore[arg-type]
        active_model_profile_id=str(structured["active_model_profile_id"] or "") or None,
        env_vars=structured["env_vars"],  # type: ignore[arg-type]
        env_path=settings.APP_ENV_PATH,
    )


@router.get("/workflow-templates")
def list_workflow_templates():
    return store.get_templates()
