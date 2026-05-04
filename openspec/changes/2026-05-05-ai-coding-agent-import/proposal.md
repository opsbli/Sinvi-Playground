# AI Coding Agent Import

## Why
- `ai_coding/worker/agents/*.md` 当前是文件 prompt，无法被 playground 的 agent 管理和 workflow/pipeline stage 直接引用。
- pipeline 执行需要 `designer`、`reviewer`、`coder`、`validator` 作为数据库中的稳定 agent。

## Scope
- 新增导入器，把四个 agent prompt 写入 agent 表。
- 为导入的 agent 增加来源和角色元数据。
- 提供可重复运行的 seed/import 行为，避免重复创建。

## Non-Goals
- 不执行 agent。
- 不迁移 story 状态。
- 不修改现有 agent CRUD 的外部行为。

## Acceptance Criteria
- 四个 `ai_coding` 角色 agent 能稳定入库。
- 重复导入不会产生重复 agent。
- pipeline stage 可以引用导入后的 agent id。
