## Context

当前前端由 `App.vue` 管理全局状态与导航，`AgentsPage`、`WorkflowsPage`、`PlaygroundPage` 分别覆盖 agent 管理、workflow 管理和即时运行。Pipeline 已在后端独立建模，因此 UI 应以独立页面呈现，避免把长流程状态塞进 workflow 列表。

## UI Design Decisions

- 新页面采用三段工作台布局：左侧 pipeline definitions，中间 brief/story 操作，右侧 run detail 与 artifacts。
- 沿用现有 glass-panel、chip、primary-button、text-button、trace-empty 等视觉语言，不引入新字体或全新主题。
- Stage 状态使用清晰的状态 chip：`pending`、`running`、`completed`、`blocked`、`failed`。
- Artifact 以类型分组卡片展示，内容使用 plain text/markdown 预览，避免在本次变更中引入复杂编辑器。
- 页面空状态必须说明下一步操作：先 bootstrap，再生成 PRD/story，再运行 story pipeline。

## Backend Decisions

- `POST /api/pipelines/ai-coding/bootstrap` 负责种子化必要 agents 与两个 pipeline definitions。
- `POST /api/pipelines/prd-story-generation` 负责从 brief 创建 PRD/story artifacts，并返回完整 run detail。
- `POST /api/pipelines/runs/{run_id}/execute-sequential` 负责执行现有 sequential run，并返回更新后的 run detail。
- Bootstrap 使用幂等查找，避免每次进入页面重复创建 definitions 或 agents。

## Data Safety

- Bootstrap 只按固定 `name + kind` 查找或创建 pipeline definitions，不更新用户自建 definitions。
- 内置 execution agents 仅在缺失时创建；已有同名 agents 会被复用。
- Sequential execution 只操作目标 run 的 stage/artifact/status。
