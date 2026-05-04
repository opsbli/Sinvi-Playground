# Runs Route Split

## Why
- `backend/app/routes.py` 里剩余的 runs 与 streaming 逻辑已经是最大的一块职责，继续保留会让主路由文件再次膨胀。
- runs 端点主要负责 workflow 调度、conversation 写入和 SSE 封装，适合独立成模块。
- 这是一次内部重组，不改变 `/api/runs` 和 `/api/runs/stream` 的对外行为。

## Scope
- 把 runs 相关路由提取到 `backend/app/routes_runs.py`。
- `backend/app/routes.py` 只保留 include runs router 的集成代码。
- 增加一个直接验证 runs 路由 helper 的回归测试。

## Non-Goals
- 不修改 workflow 执行实现或 route selection 逻辑。
- 不调整 conversation 数据模型或 message 落库语义。
- 不引入新的 runs 功能。

## Acceptance Criteria
- `/api/runs`、`/api/runs/stream` 的行为保持不变。
- 现有 `backend/tests/test_runs_api.py` 继续通过。
- 新增的 helper 测试可直接验证 dispatch 和 conversation 写入行为。
