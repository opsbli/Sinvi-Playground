# Skills Route Split

## Why
- `backend/app/routes.py` 已经把 health、settings、skills、agents、workflows、runs 和 conversations 全堆在一起，skills 相关分支最容易单独抽出。
- skills 路由同时依赖 `store.py`、`skillhub_client.py` 和 `llm_gateway`，适合先拆成独立模块，减少主路由文件体积。
- 这是一个内部重组，不改变 `/api/skills`、`/api/skills/{id}/install` 和 `/api/skills/sync` 的外部行为。

## Scope
- 把 skills 相关路由提取到 `backend/app/routes_skills.py`。
- `backend/app/routes.py` 只保留 APIRouter 组装并 include skills router。
- 增加直接验证 skills 端点行为的回归测试。

## Non-Goals
- 不改 agents、workflows、runs 或 conversations 的路由行为。
- 不修改 skillhub API 协议或 skill package 安装语义。
- 不重构 store 或 skillhub_client 的内部实现。

## Acceptance Criteria
- `/api/skills`、`/api/skills/{skill_id}/install`、`/api/skills/sync` 的行为与返回结构保持不变。
- `backend/tests/test_skills_api.py` 可以覆盖技能列表、安装和同步的关键路径。
- `python -m pytest backend/tests -q` 继续通过。
