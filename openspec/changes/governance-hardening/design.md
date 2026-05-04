# Governance Hardening Design

## 目标
- 先把后端回归测试补齐，再把 `runtime.py` 里最明显的内部 helper 拆开，降低后续治理修改的回归风险。
- 保持对外 API、workflow trace 和 conversation 行为不变，只调整内部组织方式。

## 设计决策
- 测试层使用 `TestClient` + 临时 `APP_HOME` / `APP_ENV_PATH` 隔离 SQLite 和 `.env`，避免污染开发环境。
- `runtime.py` 继续作为运行时编排入口，但把环境变量加载、PATH 组装和 LLM 相关 alias 处理收敛到 `runtime_env.py`。
- 把 fallback 路由、fallback agent 回复、任务解析和 supervisor decision 解析收敛到 `runtime_fallbacks.py`。
- `runtime.py` 只保留面向 `LLMGateway` 的主流程、工具执行和编排逻辑，减少单文件膨胀。

## 行为边界
- 这次拆分不引入新的公开 API。
- 不改变现有 workflow 的 trace 事件名、graph 结构或 `final_answer` 生成方式。
- 不修改 settings 持久化语义，也不触碰 store/schema 行为。

## 风险与验证
- 主要风险是 helper 拆分后出现导入循环或环境默认值漂移。
- 用 `pytest backend/tests -q` 验证现有 API 回归测试与 workflow 契约测试继续通过。
