from __future__ import annotations

import os

from app.settings_env import load_bootstrap_env_files, read_app_env_file, write_app_env_values


def test_write_app_env_values_round_trip(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = write_app_env_values(env_path, {"OPENAI_API_KEY": "test-key"})

    assert result == env_path
    assert env_path.read_text(encoding="utf-8") == "OPENAI_API_KEY=test-key\n"
    assert read_app_env_file(env_path) == {"OPENAI_API_KEY": "test-key"}
    assert os.environ["OPENAI_API_KEY"] == "test-key"


def test_load_bootstrap_env_files_uses_each_unique_path(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / "bootstrap.env"
    env_path.write_text("BOOTSTRAP_KEY=bootstrap-value\n", encoding="utf-8")
    monkeypatch.delenv("BOOTSTRAP_KEY", raising=False)

    load_bootstrap_env_files([env_path, env_path])

    assert os.environ["BOOTSTRAP_KEY"] == "bootstrap-value"
