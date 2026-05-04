# Agents Route Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 agents 相关 HTTP 端点从 `routes.py` 中拆到独立模块，保持现有 API 行为不变并继续缩小主路由文件复杂度。

**Architecture:** `backend/app/routes.py` 只保留 APIRouter 组装和模块 include；`backend/app/routes_agents.py` 持有 agents 列表、创建、更新、删除端点以及 skill 校验 helper。测试层新增一个直接调用 routes helper 的单测，再跑完整 backend 回归，确保拆分没有改变 HTTP 行为。

**Tech Stack:** Python, FastAPI, pytest, TestClient, monkeypatch.

---

### Task 1: 覆盖 agents route helper

**Files:**
- Create: `backend/tests/test_agents_routes.py`

- [x] **Step 1: 写出失败测试**

```python
def test_agents_route_helpers_cover_validation_and_delete_rules(monkeypatch):
    ...
```

- [x] **Step 2: 运行测试确认失败**

Run: `python -m pytest backend/tests/test_agents_routes.py -q`
Expected: fail because `routes_agents.py` does not exist yet.

### Task 2: 抽出 agents router

**Files:**
- Create: `backend/app/routes_agents.py`
- Modify: `backend/app/routes.py`

- [x] **Step 1: 搬出 agents 端点实现**

Move the following functions into `routes_agents.py`:
```python
_validate_skill_ids
list_agents
create_agent
update_agent
delete_agent
```

- [x] **Step 2: 在主路由里挂载子 router**

```python
from .routes_agents import router as agents_router

router = APIRouter(prefix="/api")
router.include_router(agents_router)
```

- [x] **Step 3: 运行 agents route 测试**

Run: `python -m pytest backend/tests/test_agents_routes.py -q`
Expected: pass.

### Task 3: 回归验证

**Files:**
- Modify: `backend/tests/test_agents_api.py`

- [x] **Step 1: 运行完整后端测试**

Run: `python -m pytest backend/tests -q`
Expected: all backend tests pass after the route split.
