from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .settings_env import read_app_env_file, write_app_env_values


def default_structured_settings(
    openai_api_key: str,
    openai_base_url: str,
    openai_model: str,
) -> dict[str, object]:
    return {
        "model_profiles": [
            {
                "id": "default",
                "provider": "custom",
                "name": "Default",
                "api_key": openai_api_key,
                "base_url": openai_base_url,
                "model": openai_model,
            }
        ],
        "active_model_profile_id": "default",
        "env_vars": [],
    }


def _normalize_model_profiles(raw_profiles: object, default_profile: dict[str, str]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not isinstance(raw_profiles, list):
        raw_profiles = []
    for index, item in enumerate(raw_profiles):
        if not isinstance(item, dict):
            continue
        profile_id = str(item.get("id") or f"profile_{index + 1}").strip() or f"profile_{index + 1}"
        normalized.append(
            {
                "id": profile_id,
                "provider": str(item.get("provider") or "custom").strip() or "custom",
                "name": str(item.get("name") or f"Profile {index + 1}").strip() or f"Profile {index + 1}",
                "api_key": str(item.get("api_key") or "").strip(),
                "base_url": str(item.get("base_url") or "https://api.openai.com/v1").strip()
                or "https://api.openai.com/v1",
                "model": str(item.get("model") or "gpt-4o-mini").strip() or "gpt-4o-mini",
            }
        )
    if normalized:
        return normalized
    return [default_profile]


def _normalize_env_vars(raw_env_vars: object) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not isinstance(raw_env_vars, list):
        return normalized
    seen: set[str] = set()
    for item in raw_env_vars:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "key": key,
                "value": str(item.get("value") or ""),
            }
        )
    return normalized


def normalize_structured_settings(
    raw: dict[str, object] | None = None,
    *,
    default_profile: dict[str, str],
) -> dict[str, object]:
    payload = raw or {"model_profiles": [default_profile], "active_model_profile_id": "default", "env_vars": []}
    model_profiles = _normalize_model_profiles(payload.get("model_profiles"), default_profile)
    active_model_profile_id = str(payload.get("active_model_profile_id") or "").strip() or model_profiles[0]["id"]
    if active_model_profile_id not in {profile["id"] for profile in model_profiles}:
        active_model_profile_id = model_profiles[0]["id"]
    env_vars = _normalize_env_vars(payload.get("env_vars"))
    return {
        "model_profiles": model_profiles,
        "active_model_profile_id": active_model_profile_id,
        "env_vars": env_vars,
    }


def _resolve_active_profile(
    payload: dict[str, object],
    *,
    default_profile: dict[str, str],
) -> dict[str, str]:
    normalized = normalize_structured_settings(payload, default_profile=default_profile)
    active_id = str(normalized["active_model_profile_id"])
    profiles = normalized["model_profiles"]
    for profile in profiles:  # type: ignore[assignment]
        if profile["id"] == active_id:
            return profile
    return profiles[0]  # type: ignore[index]


def apply_structured_settings(
    previous_payload: dict[str, object] | None,
    current_payload: dict[str, object],
    *,
    env_path: Path,
    default_profile: dict[str, str],
    reload_settings_fn: Callable[[], None] | None = None,
) -> Path:
    previous = normalize_structured_settings(previous_payload, default_profile=default_profile)
    current = normalize_structured_settings(current_payload, default_profile=default_profile)
    previous_keys = {
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        *[item["key"] for item in previous["env_vars"]],  # type: ignore[index]
    }
    active_profile = _resolve_active_profile(current, default_profile=default_profile)
    managed_values = {
        "OPENAI_API_KEY": active_profile["api_key"],
        "OPENAI_BASE_URL": active_profile["base_url"],
        "OPENAI_MODEL": active_profile["model"],
    }
    for item in current["env_vars"]:  # type: ignore[index]
        managed_values[str(item["key"])] = str(item["value"])

    existing = read_app_env_file(env_path)
    merged = {key: value for key, value in existing.items() if key not in previous_keys}
    merged.update(managed_values)
    write_app_env_values(env_path, merged)

    for key in previous_keys:
        if key not in managed_values and key in os.environ:
            os.environ.pop(key, None)
    for key, value in managed_values.items():
        os.environ[key] = str(value or "")

    if reload_settings_fn is not None:
        reload_settings_fn()
    return env_path
