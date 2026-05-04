# Runs Route Split Design

## 目标
- 将 runs 与 streaming 的 HTTP 端点从 `routes.py` 中抽离，继续缩减主路由文件复杂度。
- 保持当前 API 行为、事件流格式和 conversation 写入语义不变，只改模块组织。

## 设计决策
- 新增 `backend/app/routes_runs.py` 持有 runs 与 SSE streaming 端点，以及 `_dispatch_run` helper。
- `backend/app/routes.py` 只保留 `APIRouter` 组装并 include runs router。
- runs 路由继续直接调用 `store` 和 workflow runner，避免引入额外 service 层。

## 行为边界
- workflow 不存在时仍返回 404。
- 创建新 conversation 的逻辑保持不变。
- SSE 仍输出 `trace`、`final`、`error` 和 `end` 事件。

## 验证
- 用 helper 测试覆盖 dispatch 和 conversation 写入。
- 再跑完整后端测试，确认 HTTP 行为没变化。
