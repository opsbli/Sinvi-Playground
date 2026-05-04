# Tasks

- [x] 新增 `backend/app/settings_env.py`，提取 bootstrap、`.env` 读取和 `.env` 写入 helper。
- [x] 新增 `backend/app/settings_structured.py`，提取 structured settings 默认值、规范化和写回逻辑。
- [x] 修改 `backend/app/settings_bridge.py`，改为调用新的 helper 模块并保持现有行为不变。
- [x] 新增 `backend/tests/test_settings_env.py` 和 `backend/tests/test_settings_structured.py`，直接验证 helper 行为。
- [x] 运行 `pytest backend/tests -q` 并确认通过。
