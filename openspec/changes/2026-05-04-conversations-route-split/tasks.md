# Tasks

- [x] 新增 `backend/tests/test_conversations_api.py`，覆盖会话创建、读取、列表与删除。
- [x] 新增 `backend/app/routes_conversations.py`，把 conversations 相关端点从 `routes.py` 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include conversations router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
