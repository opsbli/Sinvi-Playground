# Tasks

- [x] 新增 `backend/app/store_schema.py`，提取 `ensure_column` 和 `initialize_schema`，保持原有表结构与索引不变。
- [x] 修改 `backend/app/store.py`，让 `_init_db` 调用新的 schema helper，并移除重复的 schema SQL。
- [x] 新增 `backend/tests/test_store_schema.py`，用临时 SQLite 数据库直接验证 schema helper。
- [x] 运行 `pytest backend/tests -q` 并确认通过。
