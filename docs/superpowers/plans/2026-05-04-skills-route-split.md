# Skills Route Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 skills 相关 HTTP 端点从 `routes.py` 中拆到独立模块，保持现有 API 行为不变并降低主路由文件复杂度。

**Architecture:** `backend/app/routes.py` 只保留 APIRouter 组装和模块 include；`backend/app/routes_skills.py` 持有 skills 列表、创建、安装和同步端点，以及必要的本地 helper。测试层直接走 FastAPI `TestClient` 覆盖 skills 关键路径，并用 monkeypatch 隔离 `skillhub_client` 和 `store`。

**Tech Stack:** Python, FastAPI, pytest, TestClient, monkeypatch.

---

### Task 1: 写 skills API 回归测试

**Files:**
- Create: `backend/tests/test_skills_api.py`

- [x] **Step 1: 写出失败测试**

```python
def test_skills_api_supports_list_create_install_and_sync(api_client, monkeypatch):
    ...
```

- [x] **Step 2: 运行测试确认失败**

Run: `python -m pytest backend/tests/test_skills_api.py -q`
Expected: fail because `routes_skills.py` does not exist yet.

- [x] **Step 3: 写最小测试数据**

Use a fake store and fake SkillHub client to exercise:
```python
GET /api/skills
POST /api/skills
POST /api/skills/{skill_id}/install
POST /api/skills/sync
```

- [x] **Step 4: 运行测试确认仍然失败**

Run: `python -m pytest backend/tests/test_skills_api.py -q`
Expected: fail with import error until route module is added.

### Task 2: 抽出 skills router

**Files:**
- Create: `backend/app/routes_skills.py`
- Modify: `backend/app/routes.py`

- [x] **Step 1: 搬出 skills 端点实现**

Move the following functions and their local helper logic into `routes_skills.py`:
```python
list_skills
create_skill
install_skill
sync_skills
```

- [x] **Step 2: 在主路由里挂载子 router**

```python
from .routes_skills import router as skills_router

router = APIRouter(prefix="/api")
router.include_router(skills_router)
```

- [x] **Step 3: 运行 skills API 测试**

Run: `python -m pytest backend/tests/test_skills_api.py -q`
Expected: pass.

### Task 3: 回归验证

**Files:**
- Modify: `backend/tests/test_skills_api.py`

- [x] **Step 1: 运行完整后端测试**

Run: `python -m pytest backend/tests -q`
Expected: all backend tests pass after the route split.
