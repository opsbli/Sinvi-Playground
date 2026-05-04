# Agents Route Split Design

## 目标
- 将 agents 相关 HTTP 端点从 `routes.py` 中抽离，进一步削减主路由文件复杂度。
- 保持当前 API 行为和错误语义不变，只改模块组织。

## 设计决策
- 新增 `backend/app/routes_agents.py` 持有 agents 列表、创建、更新、删除端点以及 `_validate_skill_ids` helper。
- `backend/app/routes.py` 只保留 `APIRouter` 组装并 include agents router。
- agents 路由继续直接调用 `store`，避免引入额外 service 层。

## 行为边界
- skill ID 不存在时仍返回 400。
- 删除 agent 时若仍被非 `single_agent_chat` workflow 使用，仍返回 409。
- 仍保留自动清理 `single_agent_chat` workflow 的行为。

## 验证
- 用路由 helper 测试覆盖 skill 校验、创建、更新和删除。
- 再跑完整后端测试，确认 HTTP 行为没变化。
