# Settings Route Split Design

## 目标
- 将 settings 相关 HTTP 端点从 `routes.py` 中抽离，进一步缩减主路由文件复杂度。
- 保持当前 API 行为和结构化配置语义不变，只改模块组织。

## 设计决策
- 新增 `backend/app/routes_settings.py` 持有 settings GET/PUT 端点。
- `backend/app/routes.py` 只保留 `APIRouter` 组装并 include settings router。
- settings 路由继续直接调用 `store`、`settings_bridge` 和 `llm_gateway`，避免引入额外 service 层。

## 行为边界
- GET `/api/settings` 仍返回 normalized payload 和 `env_path`。
- PUT `/api/settings` 仍会持久化 payload、应用 env 写回并刷新 LLM client。
- 响应结构保持 `AppSettings` 不变。

## 验证
- 用 helper 测试覆盖 normalized payload 读取和更新行为。
- 再跑完整后端测试，确认 HTTP 行为没变化。
