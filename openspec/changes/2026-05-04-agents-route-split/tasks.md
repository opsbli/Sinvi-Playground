# Tasks

- [x] 新增 `backend/tests/test_agents_routes.py`，覆盖 agents 路由 helper 的 skill 校验、创建、更新与删除分支。
- [x] 新增 `backend/app/routes_agents.py`，把 agents 相关端点和 helper 从 `routes.py` 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include agents router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
