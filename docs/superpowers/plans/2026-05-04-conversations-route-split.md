# Conversations Route Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 conversations 相关 HTTP 端点从 `routes.py` 中拆到独立模块，保持现有 API 行为不变并继续缩小主路由文件复杂度。

**Architecture:** `backend/app/routes.py` 只保留 APIRouter 组装和模块 include；`backend/app/routes_conversations.py` 持有 conversations 列表、创建、详情和删除端点。测试层继续使用现有 `api_client` fixture 覆盖 conversations 的关键路径。

**Tech Stack:** Python, FastAPI, pytest, TestClient.

---

### Task 1: 覆盖 conversations API

**Files:**
- Modify: `backend/tests/test_conversations_api.py`

- [x] **Step 1: 写出失败测试**

```python
def test_conversations_api_supports_crud(api_client):
    ...
```

- [x] **Step 2: 运行测试确认失败**

Run: `python -m pytest backend/tests/test_conversations_api.py -q`
Expected: fail because conversations routes are not split yet.

### Task 2: 抽出 conversations router

**Files:**
- Create: `backend/app/routes_conversations.py`
- Modify: `backend/app/routes.py`

- [x] **Step 1: 搬出 conversations 端点实现**

Move the following functions into `routes_conversations.py`:
```python
list_conversations
create_conversation
get_conversation
delete_conversation
```

- [x] **Step 2: 在主路由里挂载子 router**

```python
from .routes_conversations import router as conversations_router

router = APIRouter(prefix="/api")
router.include_router(conversations_router)
```

- [x] **Step 3: 运行 conversations API 测试**

Run: `python -m pytest backend/tests/test_conversations_api.py -q`
Expected: pass.

### Task 3: 回归验证

**Files:**
- Modify: `backend/tests/test_conversations_api.py`

- [x] **Step 1: 运行完整后端测试**

Run: `python -m pytest backend/tests -q`
Expected: all backend tests pass after the route split.
