# Tasks

- [x] 新增 `backend/tests/test_settings_routes.py`，覆盖 settings 路由 helper 的读取和更新分支。
- [x] 新增 `backend/app/routes_settings.py`，把 settings 相关端点从 `routes.py` 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include settings router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
