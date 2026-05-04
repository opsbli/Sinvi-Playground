# Tasks

- [x] 新增 `backend/tests/test_skills_api.py`，覆盖 skills 列表、创建、本地安装、SkillHub 安装和同步的关键路径。
- [x] 新增 `backend/app/routes_skills.py`，把 `routes.py` 中的 skills 相关端点和 helper 抽出。
- [x] 修改 `backend/app/routes.py`，只保留 include skills router 的集成代码。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
