# Workflows Route Split

## Why
- `backend/app/routes.py` 里 workflows 相关端点已经是剩余的主要聚合块，继续保留在主路由文件里会放大阅读和维护成本。
- workflows 端点主要做 CRUD 和图构建分发，不直接承担 runs 执行逻辑，适合先独立成模块。
- 这是一次内部重组，不改变 `/api/workflows` 和 `/api/workflows/{workflow_id}/graph` 的对外行为。

## Scope
- 把 workflows 相关路由提取到 `backend/app/routes_workflows.py`。
- `backend/app/routes.py` 只保留 include workflows router 的集成代码。
- 增加一个直接验证 workflows 路由 helper 的回归测试。

## Non-Goals
- 不修改 runs、streaming 或 workflow 执行调度逻辑。
- 不调整 workflow 数据模型或 store 的业务语义。
- 不引入新的 workflow 功能。

## Acceptance Criteria
- `/api/workflows`、`/api/workflows/{workflow_id}`、`/api/workflows/{workflow_id}/graph` 的行为保持不变。
- 现有 `backend/tests/test_workflows_api.py` 继续通过。
- 新增的 helper 测试可直接验证 workflow 创建校验和 graph dispatch。
