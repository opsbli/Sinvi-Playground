from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _install_openai_stub(monkeypatch) -> None:
    class _FakeCompletions:
        def create(self, *args, **kwargs):  # noqa: ANN001
            raise RuntimeError("OpenAI SDK is not available in the test environment.")

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeOpenAI:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.chat = _FakeChat()

    module = types.ModuleType("openai")
    module.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    app_home = tmp_path / "app-home"
    env_path = tmp_path / ".env"

    monkeypatch.setenv("AGENT_PLAYGROUND_APP_HOME", str(app_home))
    monkeypatch.setenv("AGENT_PLAYGROUND_ENV_PATH", str(env_path))
    monkeypatch.setenv("AGENT_PLAYGROUND_BUNDLED_SKILLS_ROOT", str(PROJECT_ROOT / "skills"))
    monkeypatch.setenv("AGENT_PLAYGROUND_BUNDLED_RUNTIME_ROOT", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    _install_openai_stub(monkeypatch)

    for module_name in [name for name in sys.modules if name == "app" or name.startswith("app.")]:
        sys.modules.pop(module_name, None)

    from app.main import app

    with TestClient(app) as client:
        yield client
