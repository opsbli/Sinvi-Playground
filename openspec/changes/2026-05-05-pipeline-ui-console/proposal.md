## Why

- Pipeline 领域已经具备后端定义、run、stage 和 artifact 底座，但前端没有入口，用户无法在界面上使用 `PRD -> Story -> Designer -> Reviewer -> Coder -> Validator` 流程。
- 现有 `Workflows` 页面面向对话型 workflow，不适合承载长生命周期 pipeline 的阶段状态、产物和重试语义。

## Scope

- 新增 `Pipelines` 前端页面，提供 pipeline template、brief 输入、story queue、run stage 和 artifact 查看。
- 在 `frontend/src/api.js` 增加 pipeline API 封装，并在 `App.vue` 增加导航与状态管理。
- 后端补充最小 pipeline action API：bootstrap AI Coding pipeline、生成 PRD/story、执行 sequential story run。
- 增加 API 与前端构建验证。

## Non-Goals

- 不做拖拽式 pipeline 编排。
- 不替换现有 `Workflow` / `Playground` 对话运行模式。
- 不接入真实代码写入执行器；本次 sequential action 先落地可观察的阶段产物闭环。
- 不做历史运行高级筛选或批量迁移 UI。

## Acceptance Criteria

- 用户能从导航进入 `Pipelines` 页面。
- 用户能点击 bootstrap 创建或复用 AI Coding pipeline definitions。
- 用户能输入 brief 生成 PRD 与 Story artifacts。
- 用户能从 Story artifact 创建并执行 sequential run，查看每个 stage 状态和 artifact。
- 未知用户自建 workflow/agent 行为不受影响。
