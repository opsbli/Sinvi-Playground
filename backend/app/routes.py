from __future__ import annotations

from fastapi import APIRouter

from .routes_agents import router as agents_router
from .routes_conversations import router as conversations_router
from .routes_runs import router as runs_router
from .routes_settings import router as settings_router
from .routes_skills import router as skills_router
from .routes_workflows import router as workflows_router


router = APIRouter(prefix="/api")
router.include_router(agents_router)
router.include_router(skills_router)
router.include_router(conversations_router)
router.include_router(workflows_router)
router.include_router(runs_router)
router.include_router(settings_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/workflow-templates")
def list_workflow_templates():
    from .store import store

    return store.get_templates()
