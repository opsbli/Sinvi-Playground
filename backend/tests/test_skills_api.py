from __future__ import annotations

import importlib
from types import SimpleNamespace

from app.schemas import SkillDefinition
from app.skillhub_client import MarketplaceSkill


def _make_local_skill(skill_id: str = "skill-local") -> SkillDefinition:
    return SkillDefinition(
        id=skill_id,
        name="Local Skill",
        description="Local skill for regression tests.",
        instruction="Follow the local skill instructions.",
        source_provider=None,
        source_skill_id=None,
        tool=None,
        local_path="/tmp/local-skill",
        runtime_preflight=None,
    )


def _make_marketplace_skill() -> MarketplaceSkill:
    return MarketplaceSkill(
        source_skill_id="remote-skill-1",
        name="Remote Skill",
        description="Remote skill from SkillHub.",
        instruction="Use the remote skill responsibly.",
        tool={
            "name": "remote-tool",
            "description": "Remote tool",
            "input_schema": {"type": "object", "properties": {}},
            "command": ["python", "tool.py"],
            "timeout_seconds": 20,
        },
        package_files={
            "SKILL.md": "# Remote Skill\n",
            "scripts/run.py": "print('ok')\n",
        },
    )


class FakeStore:
    def __init__(self) -> None:
        self.skills = {
            "skill-local": _make_local_skill(),
            "skill-hub": SkillDefinition(
                id="skill-hub",
                name="SkillHub Skill",
                description="SkillHub-installed skill.",
                instruction="Original instruction.",
                source_provider="skillhub",
                source_skill_id="remote-skill-1",
                tool=None,
                local_path="/tmp/skillhub-skill",
                runtime_preflight=None,
            ),
        }
        self.created_payloads: list[dict[str, object]] = []
        self.install_calls: list[dict[str, object]] = []
        self.sync_calls: list[dict[str, object]] = []

    def list_skills(self) -> list[SkillDefinition]:
        return [self.skills["skill-local"]]

    def create_skill(self, payload):
        self.created_payloads.append(payload.model_dump())
        return SkillDefinition(id="skill-created", **payload.model_dump())

    def get_skill(self, skill_id: str):
        return self.skills.get(skill_id)

    def install_skill_package(self, **kwargs):  # noqa: ANN003
        self.install_calls.append(kwargs)
        return SkillDefinition(
            id=str(kwargs["skill_id"]),
            name=str(kwargs["name"]),
            description=str(kwargs["description"]),
            instruction=str(kwargs["instruction"]),
            source_provider="skillhub",
            source_skill_id="remote-skill-1",
            tool=kwargs.get("tool"),
            local_path="/tmp/installed-skill",
            runtime_preflight=None,
        )

    def upsert_marketplace_skills(self, **kwargs):  # noqa: ANN003
        self.sync_calls.append(kwargs)
        return 1, 2


def _routes_skills_module():
    return importlib.import_module("app.routes_skills")


def test_skills_api_lists_and_creates_skills(api_client, monkeypatch):
    routes_skills = _routes_skills_module()
    fake_store = FakeStore()
    fake_gateway = SimpleNamespace(
        build_skill_preflight=lambda skill: {"status": "ok", "skill_id": skill.id}
    )
    monkeypatch.setattr(routes_skills, "store", fake_store)
    monkeypatch.setattr(routes_skills, "llm_gateway", fake_gateway)

    list_response = api_client.get("/api/skills")
    assert list_response.status_code == 200
    assert list_response.json()[0]["runtime_preflight"] == {"status": "ok", "skill_id": "skill-local"}

    create_response = api_client.post(
        "/api/skills",
        json={
            "name": "Created Skill",
            "description": "Created in test",
            "instruction": "Use carefully.",
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["id"] == "skill-created"


def test_skills_api_installs_local_skill_without_downloads(api_client, monkeypatch):
    routes_skills = _routes_skills_module()
    fake_store = FakeStore()
    monkeypatch.setattr(routes_skills, "store", fake_store)

    response = api_client.post("/api/skills/skill-local/install")

    assert response.status_code == 200
    assert response.json() == {
        "skill_id": "skill-local",
        "skill_name": "Local Skill",
        "source_provider": None,
        "source_skill_id": None,
        "downloaded_files": 0,
        "tool_enabled": False,
        "message": "Local skill is ready.",
    }


def test_skills_api_installs_skillhub_package(api_client, monkeypatch):
    routes_skills = _routes_skills_module()
    fake_store = FakeStore()
    fake_skillhub_client = SimpleNamespace(fetch_skill_package=lambda source_skill_id: _make_marketplace_skill())
    monkeypatch.setattr(routes_skills, "store", fake_store)
    monkeypatch.setattr(routes_skills, "skillhub_client", fake_skillhub_client)

    response = api_client.post("/api/skills/skill-hub/install")

    assert response.status_code == 200
    payload = response.json()
    assert payload["skill_id"] == "skill-hub"
    assert payload["downloaded_files"] == 2
    assert payload["tool_enabled"] is True
    assert fake_store.install_calls[0]["skill_id"] == "skill-hub"


def test_skills_api_syncs_skillhub_skills(api_client, monkeypatch):
    routes_skills = _routes_skills_module()
    fake_store = FakeStore()
    fake_skillhub_client = SimpleNamespace(fetch_skills=lambda query, limit: [_make_marketplace_skill()])
    monkeypatch.setattr(routes_skills, "store", fake_store)
    monkeypatch.setattr(routes_skills, "skillhub_client", fake_skillhub_client)

    response = api_client.post(
        "/api/skills/sync",
        json={"provider": "skillhub", "query": "remote", "limit": 5},
    )

    assert response.status_code == 200
    assert response.json() == {
        "provider": "skillhub",
        "query": "remote",
        "fetched": 1,
        "imported": 1,
        "updated": 2,
    }
    assert fake_store.sync_calls[0]["source_provider"] == "skillhub"
