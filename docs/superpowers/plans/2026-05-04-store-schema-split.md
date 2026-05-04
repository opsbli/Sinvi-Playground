# Store Schema Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `store.py` 中的数据库 schema/bootstrap 逻辑拆到独立模块，保持行为不变并降低单文件复杂度。

**Architecture:** `store.py` 保留 `SQLitePlaygroundStore` 的业务入口、文件技能同步和 CRUD 行为；`backend/app/store_schema.py` 只负责 SQLite 表结构、列补齐与索引创建。测试层用独立的临时 SQLite 连接直接验证 schema helper，再跑完整 API 回归确保没有行为漂移。

**Tech Stack:** Python, sqlite3, pytest, FastAPI TestClient.

---

### Task 1: 提取 schema helper

**Files:**
- Create: `backend/app/store_schema.py`
- Modify: `backend/app/store.py`

- [x] **Step 1: 写出最小 schema 测试**

```python
def test_initialize_schema_creates_core_tables_and_indexes():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    ...
```

- [x] **Step 2: 实现 schema helper**

Move the `CREATE TABLE`, `CREATE INDEX`, and `ALTER TABLE` logic into `store_schema.py` without changing table names, column names, or defaults.

- [x] **Step 3: 运行测试确认通过**

Run: `python -m pytest backend/tests/test_store_schema.py -q`
Expected: `1 passed`

### Task 2: 回归验证

**Files:**
- Modify: `backend/tests/test_store_schema.py`
- Modify: `backend/app/store.py`

- [x] **Step 1: 运行完整回归**

Run: `python -m pytest backend/tests -q`
Expected: existing API tests still pass and the new schema test passes.
