# Tasks

- [ ] 新增 pipeline Pydantic schema，定义 definition、stage、run、artifact 的请求/响应模型。
- [ ] 扩展 SQLite schema，创建 pipeline 相关表和索引。
- [ ] 新增 pipeline store/repository 方法，覆盖 definition、run、stage run、artifact CRUD。
- [ ] 新增 `backend/app/routes_pipelines.py`，提供最小 API。
- [ ] 在主 router 中 include pipeline router。
- [ ] 新增 schema/store/API 测试。
- [ ] 运行 `python -m pytest backend/tests -q` 并确认通过。
