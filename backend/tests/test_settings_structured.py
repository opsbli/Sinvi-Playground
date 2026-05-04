from __future__ import annotations

import os

from app.settings_structured import apply_structured_settings, default_structured_settings, normalize_structured_settings


def test_normalize_structured_settings_uses_default_profile() -> None:
    default_profile = default_structured_settings("api-key", "https://example.invalid/v1", "gpt-test")["model_profiles"][0]

    payload = normalize_structured_settings({"model_profiles": []}, default_profile=default_profile)

    assert payload["active_model_profile_id"] == "default"
    assert payload["model_profiles"][0]["model"] == "gpt-test"


def test_apply_structured_settings_writes_env_and_sets_os_environ(tmp_path, monkeypatch) -> None:
    default_profile = default_structured_settings("api-key", "https://example.invalid/v1", "gpt-test")["model_profiles"][0]
    env_path = tmp_path / ".env"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_KEY", raising=False)

    apply_structured_settings(
        None,
        {
            "model_profiles": [default_profile],
            "active_model_profile_id": "default",
            "env_vars": [{"key": "CUSTOM_KEY", "value": "custom-value"}],
        },
        env_path=env_path,
        default_profile=default_profile,
        reload_settings_fn=None,
    )

    assert env_path.read_text(encoding="utf-8") == (
        "CUSTOM_KEY=custom-value\n"
        "OPENAI_API_KEY=api-key\n"
        "OPENAI_BASE_URL=https://example.invalid/v1\n"
        "OPENAI_MODEL=gpt-test\n"
    )
    assert os.environ["OPENAI_API_KEY"] == "api-key"
    assert os.environ["CUSTOM_KEY"] == "custom-value"
