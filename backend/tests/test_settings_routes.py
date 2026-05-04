from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from app.schemas import AppSettings, EnvVarEntry, ModelProfile


def _load_module():
    return importlib.import_module("app.routes_settings")


class FakeStore:
    def __init__(self) -> None:
        self.payload = {
            "model_profiles": [
                {
                    "id": "profile-1",
                    "provider": "custom",
                    "name": "Profile 1",
                    "api_key": "key-1",
                    "base_url": "https://example.invalid/v1",
                    "model": "gpt-test",
                }
            ],
            "active_model_profile_id": "profile-1",
            "env_vars": [{"key": "FOO", "value": "bar"}],
        }
        self.saved_payload = None

    def get_app_settings_payload(self):
        return self.payload

    def save_app_settings_payload(self, payload):
        self.saved_payload = payload
        self.payload = payload


def test_get_app_settings_returns_normalized_payload(monkeypatch):
    module = _load_module()
    fake_store = FakeStore()
    monkeypatch.setattr(module, "store", fake_store)
    monkeypatch.setattr(module, "settings", SimpleNamespace(APP_ENV_PATH="C:/tmp/test.env"))

    result = module.get_app_settings()

    assert result.active_model_profile_id == "profile-1"
    assert result.env_path == "C:/tmp/test.env"
    assert result.model_profiles[0].name == "Profile 1"


def test_update_app_settings_persists_and_refreshes(monkeypatch, tmp_path):
    module = _load_module()
    fake_store = FakeStore()
    env_path = tmp_path / "app.env"
    monkeypatch.setattr(module, "store", fake_store)
    monkeypatch.setattr(module, "settings", SimpleNamespace(APP_ENV_PATH=str(env_path)))

    refreshed = []

    def fake_refresh_client():
        refreshed.append(True)

    monkeypatch.setattr(module.llm_gateway, "refresh_client", fake_refresh_client)
    applied = []

    def fake_apply_structured_settings(previous_payload, current_payload):  # noqa: ANN001
        applied.append((previous_payload, current_payload))
        return env_path

    monkeypatch.setattr(module, "apply_structured_settings", fake_apply_structured_settings)

    payload = AppSettings(
        model_profiles=[
            ModelProfile(
                id="profile-2",
                provider="custom",
                name="Profile 2",
                api_key="key-2",
                base_url="https://example.invalid/v2",
                model="gpt-test-2",
            )
        ],
        active_model_profile_id="profile-2",
        env_vars=[EnvVarEntry(key="FOO", value="baz")],
        env_path=str(env_path),
    )

    result = module.update_app_settings(payload)

    assert result.active_model_profile_id == "profile-2"
    assert fake_store.saved_payload["active_model_profile_id"] == "profile-2"
    assert refreshed == [True]
    assert result.env_path == str(env_path)
    assert applied and applied[0][1]["active_model_profile_id"] == "profile-2"
