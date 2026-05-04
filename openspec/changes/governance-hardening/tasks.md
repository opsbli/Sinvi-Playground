# Tasks

- [x] 新增 `backend/tests/conftest.py`，在每个测试前创建隔离的临时 `APP_HOME` / `APP_ENV_PATH`，并返回可用的 FastAPI `TestClient`。
- [x] 新增 `backend/tests/test_health.py`，覆盖 `/api/health` 返回 `{"status":"ok"}`。
- [x] 新增 `backend/tests/test_settings_api.py`，覆盖 `/api/settings` 的读取与最小写入回归。
- [x] 新增 `backend/tests/test_agents_api.py`，覆盖智能体创建、列表、更新与删除的基础流程。
- [x] 新增 `backend/tests/test_workflows_api.py`，覆盖工作流创建与列表的基础流程。
- [x] 新增 `backend/tests/test_runs_api.py`，覆盖 `/api/runs` 的基础错误分支，避免依赖外部模型调用。
- [x] 新增 `backend/tests/test_conversations_api.py`，覆盖会话创建、读取、列表与删除。
- [x] 新增 `backend/tests/test_router_specialists_workflow.py`，覆盖 router_specialists 在无 API / fallback 条件下的 `route_selected`、`assistant_message` 与 `artifacts` 最小契约。
- [x] 新增 `backend/tests/test_workflow_contracts.py`，覆盖四类工作流的 `final_answer` / `trace` / `graph` 最小契约一致性。
- [x] 在 `backend/requirements.txt` 中加入 `pytest` 与 `httpx`。
- [x] 运行 `pytest backend/tests -q` 并确认通过。
- [x] 将 `runtime.py` 中的环境变量组装提取到 `backend/app/runtime_env.py`，并保持默认 `.env` / PATH 行为不变。
- [x] 将 `runtime.py` 中的 fallback 逻辑提取到 `backend/app/runtime_fallbacks.py`，并保持 route / agent response / parser 行为不变。
- [x] 重新运行 `pytest backend/tests -q`，确认 runtime helper 拆分没有引入回归。
