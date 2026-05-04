# Governance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立后端最小回归测试骨架，并把 `runtime.py` 中最明显的环境与 fallback helper 拆到独立模块，减少后续治理修改的回归风险。

**Architecture:** 采用黑盒 API 测试 + 每个测试独立的临时后端环境。测试层通过 `TestClient` 访问 FastAPI 应用，使用临时 `APP_HOME` 和 `APP_ENV_PATH` 隔离 SQLite 数据库与 `.env` 文件，避免污染工作区现有数据。运行时内部把环境变量组装与 fallback 逻辑拆到独立 helper 模块，`runtime.py` 保留编排入口。

**Tech Stack:** Python, pytest, FastAPI `TestClient`, 现有 SQLite store。

---

### Task 1: 写出 API 回归测试骨架

**Files:**
- Create: `.worktrees/governance-hardening/backend/tests/conftest.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_health.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_settings_api.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_agents_api.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_workflows_api.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_runs_api.py`
- Create: `.worktrees/governance-hardening/backend/tests/test_conversations_api.py`

- [ ] **Step 1: 写出失败测试**

```python
def test_health_endpoint_reports_ok(api_client):
    response = api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_health.py -q`
Expected: collection fails because `api_client` fixture is not defined yet.

- [ ] **Step 3: 写最小支撑代码**

```python
@pytest.fixture
def api_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    ...
```

- [ ] **Step 4: 运行相关测试确认通过**

Run: `pytest backend/tests -q`
Expected: all regression skeleton tests pass.

### Task 2: 补测试依赖

**Files:**
- Modify: `.worktrees/governance-hardening/backend/requirements.txt`

- [ ] **Step 1: 添加 pytest 和 httpx**

```text
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 2: 运行测试确认依赖可用**

Run: `python -m pytest backend/tests -q`
Expected: pytest can collect and execute the new test suite.

### Task 3: 拆分 runtime 内部 helper

**Files:**
- Create: `.worktrees/governance-hardening/backend/app/runtime_env.py`
- Create: `.worktrees/governance-hardening/backend/app/runtime_fallbacks.py`
- Modify: `.worktrees/governance-hardening/backend/app/runtime.py`

- [ ] **Step 1: 抽出环境变量组装 helper**

Move default env loading and PATH assembly logic into `runtime_env.py`, keep the existing env alias behavior unchanged.

- [ ] **Step 2: 抽出 fallback helper**

Move fallback route / agent response / parser logic into `runtime_fallbacks.py`, keep returned text and selection rules unchanged.

- [ ] **Step 3: 重新运行回归测试**

Run: `python -m pytest backend/tests -q`
Expected: all API and workflow regression tests still pass after the helper split.
