# Settings Bridge Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `settings_bridge.py` 中的环境文件读写与 structured settings 处理拆到独立模块，保持 `/api/settings` 行为不变。

**Architecture:** `settings_bridge.py` 继续作为 settings 协调入口，保留 `Settings` 加载与最终写回流程；`backend/app/settings_env.py` 负责 `.env` 读取、写入和默认 bootstrap；`backend/app/settings_structured.py` 负责 structured settings 的规范化与合并。测试层直接覆盖 helper 函数，再通过现有 API 测试确认行为没变。

**Tech Stack:** Python, pathlib, python-dotenv, pytest, FastAPI TestClient.

---

### Task 1: 抽出 env file helper

**Files:**
- Create: `backend/app/settings_env.py`
- Modify: `backend/app/settings_bridge.py`

- [x] **Step 1: 写出最小 helper 测试**

```python
def test_write_app_env_values_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_bridge.settings, "APP_ENV_PATH", str(tmp_path / ".env"))
    path = write_app_env_values({"OPENAI_API_KEY": "test-key"})
    assert path.read_text(encoding="utf-8").strip() == "OPENAI_API_KEY=test-key"
```

- [x] **Step 2: 实现 env helper**

Move `read_app_env_file`, `write_app_env_values`, and bootstrap loading into `settings_env.py` without changing file format or env side effects.

- [x] **Step 3: 运行测试确认通过**

Run: `python -m pytest backend/tests/test_settings_api.py -q`
Expected: existing settings API tests still pass.

### Task 2: 抽出 structured settings helper

**Files:**
- Create: `backend/app/settings_structured.py`
- Modify: `backend/app/settings_bridge.py`

- [x] **Step 1: 写出 structured settings helper 测试**

```python
def test_normalize_structured_settings_uses_default_profile():
    payload = normalize_structured_settings({"model_profiles": []})
    assert payload["active_model_profile_id"] == "default"
```

- [x] **Step 2: 实现 structured helper**

Move `default_structured_settings`, `_normalize_model_profiles`, `_normalize_env_vars`, `normalize_structured_settings`, `_resolve_active_profile`, and `apply_structured_settings` into `settings_structured.py`.

- [x] **Step 3: 运行完整回归**

Run: `python -m pytest backend/tests -q`
Expected: all backend tests continue to pass.
