# Pipeline PRD Story Generation

## Why
- `ai_coding` 的 story 依赖 PRD，现有流程依靠外部 `PRD.md` 和 `story-splitter` skill。
- 完整内化需要把 PRD 生成和 Story 拆分作为 pipeline 上游阶段。

## Scope
- 新增 `prd_writer` stage。
- 新增 `story_splitter` stage。
- 新增 PRD 和 Story artifact 类型。
- 支持从用户 brief 创建 PRD，再拆分为多个 story run。

## Non-Goals
- 不执行 designer/reviewer/coder/validator。
- 不做复杂产品管理系统。
- 不做 UI 富文本编辑器。

## Acceptance Criteria
- 输入产品 brief 可以生成 PRD artifact。
- PRD 可以拆分成多个 Story artifact。
- Story artifact 可以作为 sequential pipeline run 的输入。
