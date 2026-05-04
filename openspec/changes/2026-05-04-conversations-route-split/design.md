# Conversations Route Split Design

## 目标
- 将 conversations 相关 HTTP 端点从 `routes.py` 中抽离，继续削减主路由文件体积。
- 保持当前 API 行为、数据格式和 store 调用方式不变。

## 设计决策
- 新增 `backend/app/routes_conversations.py` 持有 conversations 路由函数。
- `backend/app/routes.py` 只保留 `APIRouter` 组装并 include conversations router。
- conversations 路由直接使用 `store`，不引入额外 service 层。

## 行为边界
- 创建会话前仍然校验 workflow 存在。
- `GET /api/conversations` 仍支持 `workflow_id` 过滤。
- `GET /api/conversations/{conversation_id}` 仍返回 `ConversationDetail`。

## 验证
- 用 API 回归测试覆盖列表、创建、详情和删除。
- 再跑完整后端测试，确认路由拆分没有回归。
