# Pipeline Core Domain

## Why
- `ai_coding` 的 `PRD -> Story -> Designer -> Reviewer -> Coder -> Validator` 是长生命周期状态机，不能继续依赖 `worker_state.json` 和 `status.json` 作为运行真相源。
- 现有 `workflow` 域适合单次请求/响应和 trace，不适合承载 story、阶段、重试、artifact 和阻断状态。
- 需要先建立独立 `pipeline` 域，作为后续 PRD 生成、Story 拆分、顺序执行和导入导出的基础。

## Scope
- 新增 pipeline 数据模型和 SQLite 表。
- 新增 pipeline repository/store 方法。
- 新增只读/创建类 API，用于创建 pipeline definition 和 pipeline run。
- 建立最小测试覆盖：schema 初始化、CRUD、状态转换基础约束。

## Non-Goals
- 不实现 LLM 执行器。
- 不实现 PRD 生成或 Story 拆分。
- 不做 UI。
- 不导入旧 `ai_coding/worker` 文件。

## Acceptance Criteria
- 数据库可以持久化 pipeline definition、stage definition、pipeline run、stage run 和 artifact。
- 可以创建一个顺序 pipeline run，并读取其阶段状态。
- 现有 workflow/agent/conversation API 行为不变。
