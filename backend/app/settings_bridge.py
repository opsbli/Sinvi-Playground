from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import os

from .settings_env import (
    load_bootstrap_env_files,
    read_app_env_file as read_app_env_file_impl,
    write_app_env_values as write_app_env_values_impl,
)
from .settings_structured import (
    apply_structured_settings as apply_structured_settings_impl,
    default_structured_settings as default_structured_settings_impl,
    normalize_structured_settings as normalize_structured_settings_impl,
)


PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
BACKEND_ROOT_PATH = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT_PATH / ".env"


def _load_bootstrap_env_files() -> None:
    env_paths: list[Path] = []
    app_env_path = str(os.getenv("AGENT_PLAYGROUND_ENV_PATH", "")).strip()
    if app_env_path:
        env_paths.append(Path(app_env_path))
    env_paths.append(ENV_PATH)

    load_bootstrap_env_files(env_paths)


_load_bootstrap_env_files()


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _load_settings_values() -> dict[str, str | int]:
    return {
        "PROJECT_ROOT": str(PROJECT_ROOT_PATH),
        "BACKEND_ROOT": str(BACKEND_ROOT_PATH),
        "APP_HOME": _env_str("AGENT_PLAYGROUND_APP_HOME", str(BACKEND_ROOT_PATH)),
        "BUNDLED_SKILLS_ROOT": _env_str(
            "AGENT_PLAYGROUND_BUNDLED_SKILLS_ROOT",
            str(BACKEND_ROOT_PATH / "skills"),
        ),
        "BUNDLED_RUNTIME_ROOT": _env_str(
            "AGENT_PLAYGROUND_BUNDLED_RUNTIME_ROOT",
            "",
        ),
        "APP_ENV_PATH": _env_str(
            "AGENT_PLAYGROUND_ENV_PATH",
            str(ENV_PATH),
        ),
        "OPENAI_API_KEY": _env_str("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": _env_str("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "OPENAI_MODEL": _env_str("OPENAI_MODEL", "gpt-4o-mini"),
        "SKILLHUB_API_KEY": _env_str("SKILLHUB_API_KEY", ""),
        "SKILLHUB_BASE_URL": _env_str("SKILLHUB_BASE_URL", "https://www.skillhub.club/api/v1"),
        "SKILLHUB_TIMEOUT_SECONDS": _env_int("SKILLHUB_TIMEOUT_SECONDS", 20),
    }


@dataclass(frozen=True)
class Settings:
    PROJECT_ROOT: str
    BACKEND_ROOT: str
    APP_HOME: str
    BUNDLED_SKILLS_ROOT: str
    BUNDLED_RUNTIME_ROOT: str
    APP_ENV_PATH: str
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL: str
    SKILLHUB_API_KEY: str
    SKILLHUB_BASE_URL: str
    SKILLHUB_TIMEOUT_SECONDS: int


settings = Settings(**_load_settings_values())


def reload_settings() -> Settings:
    values = _load_settings_values()
    for key, value in values.items():
        object.__setattr__(settings, key, value)
    return settings


def read_app_env_file() -> dict[str, str]:
    return read_app_env_file_impl(Path(settings.APP_ENV_PATH))


def default_structured_settings() -> dict[str, object]:
    return default_structured_settings_impl(
        settings.OPENAI_API_KEY,
        settings.OPENAI_BASE_URL,
        settings.OPENAI_MODEL,
    )


def normalize_structured_settings(raw: dict[str, object] | None = None) -> dict[str, object]:
    default_profile = default_structured_settings()["model_profiles"][0]  # type: ignore[index]
    return normalize_structured_settings_impl(raw, default_profile=default_profile)  # type: ignore[return-value]


def apply_structured_settings(
    previous_payload: dict[str, object] | None,
    current_payload: dict[str, object],
) -> Path:
    default_profile = default_structured_settings()["model_profiles"][0]  # type: ignore[index]
    return apply_structured_settings_impl(
        previous_payload,
        current_payload,
        env_path=Path(settings.APP_ENV_PATH),
        default_profile=default_profile,
        reload_settings_fn=reload_settings,
    )


def write_app_env_values(values: dict[str, str]) -> Path:
    env_path = write_app_env_values_impl(Path(settings.APP_ENV_PATH), values)
    reload_settings()
    return env_path
