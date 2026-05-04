# Agents Route Split

## Why
- `backend/app/routes.py` 里的 agents 端点已经相对独立，适合继续拆成单独模块，缩小主路由文件体积。
- agents 路由只依赖 `store` 和 `skill` 校验逻辑，不涉及 workflow 运行编排，风险比 runs/workflows 更低。
- 这是一次内部重组，不改变 `/api/agents` 的对外行为。

## Scope
- 把 agents 相关路由提取到 `backend/app/routes_agents.py`。
- `backend/app/routes.py` 只保留 include agents router 的集成代码。
- 增加一个直接验证 agents 路由 helper 的回归测试。

## Non-Goals
- 不修改 workflows、skills、runs 或 conversations 路由行为。
- 不调整 agent 数据模型或 store 的业务语义。
- 不引入新的 agent 功能。

## Acceptance Criteria
- `/api/agents`、`/api/agents/{agent_id}` 的行为保持不变。
- `backend/tests/test_agents_api.py` 继续通过。
- 新增的 route helper 测试可直接验证 skill ID 校验和 delete 分支。
