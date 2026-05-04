# Settings Route Split

## Why
- `backend/app/routes.py` 里剩余的 settings 端点已经足够独立，继续保留会让主路由文件维持不必要的业务细节。
- settings 端点主要负责结构化配置的读写，不参与 workflow 或 conversation 调度，适合单独成模块。
- 这是一次内部重组，不改变 `/api/settings` 的对外行为。

## Scope
- 把 settings 相关路由提取到 `backend/app/routes_settings.py`。
- `backend/app/routes.py` 只保留 include settings router 的集成代码。
- 增加一个直接验证 settings 路由 helper 的回归测试。

## Non-Goals
- 不修改 settings bridge 的 env 写回策略。
- 不调整 `AppSettings` 数据模型或结构化配置语义。
- 不引入新的 settings 功能。

## Acceptance Criteria
- `/api/settings` 的 GET 和 PUT 行为保持不变。
- 现有 `backend/tests/test_settings_api.py` 继续通过。
- 新增的 helper 测试可直接验证 normalized payload 读取和更新后的写回调用。
