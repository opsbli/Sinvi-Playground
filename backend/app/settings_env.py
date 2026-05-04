from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


def load_bootstrap_env_files(env_paths: list[Path]) -> None:
    seen: set[str] = set()
    for env_path in env_paths:
        try:
            normalized = str(env_path.resolve())
        except OSError:
            normalized = str(env_path)
        if normalized in seen:
            continue
        seen.add(normalized)
        if env_path.exists() and env_path.is_file():
            load_dotenv(env_path, override=False)


def read_app_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists() or not env_path.is_file():
        return {}
    try:
        loaded = dotenv_values(env_path)
    except Exception:  # noqa: BLE001
        return {}

    result: dict[str, str] = {}
    for key, value in loaded.items():
        key_text = str(key or "").strip()
        if not key_text:
            continue
        result[key_text] = str(value) if value is not None else ""
    return result


def write_app_env_values(env_path: Path, values: dict[str, str]) -> Path:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_app_env_file(env_path)
    merged = dict(existing)
    for key, value in values.items():
        key_text = str(key or "").strip()
        if not key_text:
            continue
        merged[key_text] = str(value or "")

    lines = [f"{key}={merged[key]}" for key in sorted(merged.keys())]
    env_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    for key, value in values.items():
        key_text = str(key or "").strip()
        if not key_text:
            continue
        os.environ[key_text] = str(value or "")

    return env_path
