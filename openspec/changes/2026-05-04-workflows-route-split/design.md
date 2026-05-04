# Workflows Route Split Design

## 目标
- 将 workflows 相关 HTTP 端点从 `routes.py` 中抽离，进一步削减主路由文件复杂度。
- 保持当前 API 行为和错误语义不变，只改模块组织。

## 设计决策
- 新增 `backend/app/routes_workflows.py` 持有 workflows 列表、创建、更新、删除和 graph 端点以及相关 helper。
- `backend/app/routes.py` 只保留 `APIRouter` 组装并 include workflows router。
- workflows 路由继续直接调用 `store` 和 graph builder，避免引入额外 service 层。

## 行为边界
- workflow 里引用不存在的 agent ID 时仍返回 400。
- workflow 类型所需的最小 agent 数量仍按 template 约束校验。
- graph endpoint 仍按 workflow.type 分发到对应 builder。

## 验证
- 用 helper 测试覆盖 workflow 创建校验和 graph dispatch。
- 再跑完整后端测试，确认 HTTP 行为没变化。
