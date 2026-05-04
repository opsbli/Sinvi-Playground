# Governance Hardening

## Why
- 需要先建立后端最小回归测试骨架，保证后续治理类修改有稳定的验证入口。
- 目前 backend 没有 `tests/` 目录，新增测试能够把健康检查、设置、智能体、工作流、运行和会话的基础 API 行为固定下来。
- 这一步本身不改变产品行为，只补充可重复执行的验证基础。
- 运行时内部 helper 过于集中，把环境组装和 fallback 逻辑拆出独立模块，可以降低 `runtime.py` 的维护成本，而不改变外部行为。

## Scope
- 新增 `backend/tests/` 下的 pytest 骨架。
- 为测试提供独立的临时后端环境，避免污染工作区内现有 SQLite 数据库和 `.env`。
- 补充 `pytest` 与 `httpx` 作为测试依赖。
- 将 `runtime.py` 中的环境变量组装与 fallback 逻辑提取到独立 helper 模块，保持原有行为不变。

## Non-Goals
- 不修改 API 行为本身。
- 不扩展为完整端到端测试套件。
- 不重构工作流协议、路由规则或对外返回结构。

## Acceptance Criteria
- `backend/tests/` 下的基础 API 测试可以在隔离环境中运行。
- `pytest backend/tests -q` 可以执行并通过。
- 新增依赖写入 `backend/requirements.txt`，后续可直接安装运行。
- `runtime.py` 仍可正常导入并维持现有行为，环境组装和 fallback helper 逻辑已拆到独立模块。
