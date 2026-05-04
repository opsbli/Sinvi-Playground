# Tasks

- [x] 新增 pipeline Pydantic schema，定义 definition、stage、run、artifact 的请求/响应模型。
- [x] 扩展 SQLite schema，创建 pipeline 相关表和索引。
- [x] 新增 pipeline store/repository 方法，覆盖 definition/run 创建读取、stage run 初始化，以及 artifact 持久化基础表/模型。
- [x] 新增 `backend/app/routes_pipelines.py`，提供最小 API。
- [x] 在主 router 中 include pipeline router。
- [x] 新增 schema/store/API 测试。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
