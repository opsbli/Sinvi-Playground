from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from dotenv import dotenv_values


def first_non_empty_env_value(env_map: Mapping[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = str(env_map.get(key, "")).strip()
        if value:
            return value
    return ""


def set_env_if_missing(env_map: dict[str, str], key: str, value: str) -> None:
    if not value:
        return
    if str(env_map.get(key, "")).strip():
        return
    env_map[key] = value


def apply_llm_env_aliases(env_map: dict[str, str]) -> dict[str, str]:
    key_value = first_non_empty_env_value(
        env_map,
        (
            "LLM_API_KEY",
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "MOONSHOT_API_KEY",
            "QWEN_API_KEY",
            "DASHSCOPE_API_KEY",
        ),
    )
    base_value = first_non_empty_env_value(
        env_map,
        (
            "LLM_BASE_URL",
            "OPENAI_BASE_URL",
            "OPENROUTER_BASE_URL",
            "MOONSHOT_BASE_URL",
            "QWEN_BASE_URL",
            "DASHSCOPE_BASE_URL",
        ),
    )
    model_value = first_non_empty_env_value(
        env_map,
        (
            "LLM_MODEL",
            "OPENAI_MODEL",
            "OPENROUTER_MODEL",
            "MOONSHOT_MODEL",
            "QWEN_MODEL",
            "DASHSCOPE_MODEL",
        ),
    )

    set_env_if_missing(env_map, "LLM_API_KEY", key_value)
    set_env_if_missing(env_map, "LLM_BASE_URL", base_value)
    set_env_if_missing(env_map, "LLM_MODEL", model_value)

    llm_key = str(env_map.get("LLM_API_KEY", "")).strip()
    llm_base = str(env_map.get("LLM_BASE_URL", "")).strip()
    llm_model = str(env_map.get("LLM_MODEL", "")).strip()

    set_env_if_missing(env_map, "OPENAI_API_KEY", llm_key)
    set_env_if_missing(env_map, "OPENAI_BASE_URL", llm_base)
    set_env_if_missing(env_map, "OPENAI_MODEL", llm_model)

    base_lower = llm_base.lower()
    if "openrouter.ai" in base_lower:
        set_env_if_missing(env_map, "OPENROUTER_API_KEY", llm_key)
        set_env_if_missing(env_map, "OPENROUTER_BASE_URL", llm_base)
        set_env_if_missing(env_map, "OPENROUTER_MODEL", llm_model)
    if "moonshot.cn" in base_lower:
        set_env_if_missing(env_map, "MOONSHOT_API_KEY", llm_key)
        set_env_if_missing(env_map, "MOONSHOT_BASE_URL", llm_base)
        set_env_if_missing(env_map, "MOONSHOT_MODEL", llm_model)
    if "dashscope.aliyuncs.com" in base_lower:
        set_env_if_missing(env_map, "QWEN_API_KEY", llm_key)
        set_env_if_missing(env_map, "QWEN_BASE_URL", llm_base)
        set_env_if_missing(env_map, "QWEN_MODEL", llm_model)
        set_env_if_missing(env_map, "DASHSCOPE_API_KEY", llm_key)
        set_env_if_missing(env_map, "DASHSCOPE_BASE_URL", llm_base)
        set_env_if_missing(env_map, "DASHSCOPE_MODEL", llm_model)
    return env_map


def load_default_runtime_env(
    *,
    base_env: Mapping[str, str],
    env_candidates: Iterable[Path],
) -> dict[str, str]:
    env_map = dict(base_env)
    seen_env_paths: set[str] = set()
    for env_path in env_candidates:
        try:
            normalized = str(env_path.resolve())
        except OSError:
            normalized = str(env_path)
        if normalized in seen_env_paths:
            continue
        seen_env_paths.add(normalized)
        if not env_path.exists() or not env_path.is_file():
            continue
        try:
            loaded = dotenv_values(env_path)
        except Exception:  # noqa: BLE001
            loaded = {}
        for key, value in loaded.items():
            key_text = str(key or "").strip()
            if not key_text:
                continue
            value_text = str(value) if value is not None else ""
            if value_text and not str(env_map.get(key_text, "")).strip():
                env_map[key_text] = value_text
    return apply_llm_env_aliases(env_map)


def build_runtime_env(
    *,
    default_env: dict[str, str],
    bundled_node_bin: Path | None,
    runtime_bin_dir: Path,
    tool_dir: Path,
) -> dict[str, str]:
    runtime_env = dict(default_env)

    path_parts: list[str] = []
    current_path = str(runtime_env.get("PATH") or "")
    if bundled_node_bin and str(bundled_node_bin) not in current_path:
        path_parts.append(str(bundled_node_bin))
    if str(runtime_bin_dir) not in current_path:
        path_parts.append(str(runtime_bin_dir))
    if str(tool_dir) not in current_path:
        path_parts.append(str(tool_dir))
    if current_path:
        path_parts.append(current_path)
    runtime_env["PATH"] = os.pathsep.join(path_parts) if path_parts else current_path
    if not str(runtime_env.get("LANG") or "").strip():
        runtime_env["LANG"] = "C.UTF-8"
    if not str(runtime_env.get("LC_ALL") or "").strip():
        runtime_env["LC_ALL"] = str(runtime_env.get("LANG") or "C.UTF-8")
    return runtime_env
