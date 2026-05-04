# Tasks

- [x] 新增 `backend/tests/test_workflow_routes.py`，覆盖 workflows 路由 helper 的创建校验和 graph dispatch 分支。
- [x] 新增 `backend/app/routes_workflows.py`，把 workflows 相关端点和 helper 从 `routes.py` 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include workflows router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
