# Tasks

- [x] 新增 `backend/tests/test_run_routes.py`，覆盖 runs 路由 helper 的 dispatch 和 conversation 写入分支。
- [x] 新增 `backend/app/routes_runs.py`，把 runs 和 streaming 相关端点从 `routes.py` 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include runs router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
