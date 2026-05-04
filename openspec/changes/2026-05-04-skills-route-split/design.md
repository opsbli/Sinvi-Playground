# Skills Route Split Design

## 目标
- 将 skills 相关 HTTP 端点从 `routes.py` 中抽离，减少主路由文件的职责密度。
- 保持当前 API 行为和依赖关系不变，只改变模块组织方式。

## 设计决策
- 新增 `backend/app/routes_skills.py` 持有 skills 相关路由函数和局部 helper。
- `backend/app/routes.py` 继续保留 `router = APIRouter(prefix="/api")`，并通过 `include_router` 挂载 skills router。
- skills 路由模块继续直接使用 `store`、`skillhub_client` 和 `llm_gateway`，避免引入额外 service 层。

## 行为边界
- `runtime_preflight` 的附加逻辑保持不变。
- skillhub 安装失败时的 HTTP 状态码与消息保持不变。
- sync 接口仍只接受 `skillhub` provider。

## 验证
- 通过 API 测试覆盖 list/create/install/sync 行为。
- 通过完整后端测试确认 route split 没有回归。
