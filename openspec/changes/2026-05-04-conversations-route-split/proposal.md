# Conversations Route Split

## Why
- `backend/app/routes.py` 里 conversations 端点已经很独立，和 skills/agents/workflows/runs 的耦合很低。
- 把 conversations 路由抽出来可以继续缩小主路由文件，降低后续治理和 review 的心智负担。
- 这是内部重组，不改变 `/api/conversations` 相关行为。

## Scope
- 把 conversations 相关路由提取到 `backend/app/routes_conversations.py`。
- `backend/app/routes.py` 只保留 include conversations router 的集成代码。
- 增加 conversations API 回归测试，覆盖 list/create/detail/delete。

## Non-Goals
- 不修改 agents、skills、workflows 或 runs 的路由行为。
- 不调整 conversation 数据模型或 store 行为。
- 不引入新的对话功能。

## Acceptance Criteria
- `/api/conversations`、`/api/conversations/{conversation_id}` 和删除接口的行为保持不变。
- `backend/tests/test_conversations_api.py` 能继续通过。
- `python -m pytest backend/tests -q` 继续通过。
