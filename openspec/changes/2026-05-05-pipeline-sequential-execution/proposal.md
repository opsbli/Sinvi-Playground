# Pipeline Sequential Execution

## Why
- `ai_coding` 的核心价值是严格顺序执行 `designer -> reviewer -> coder -> validator`，并通过阶段状态、报告和重试保证质量。
- pipeline core 只提供持久化，仍需要执行器把 stage 串起来。

## Scope
- 新增 sequential pipeline runner。
- 固定支持 `designer`、`reviewer`、`coder`、`validator` 四阶段。
- 每阶段保存 input、output、artifact、trace、attempt 和错误。
- 支持 validator 失败后回到 coder。

## Non-Goals
- 不实现 UI。
- 不替代现有 workflow runner。
- 不直接执行旧 `worker.py`。

## Acceptance Criteria
- 一个 Story 可以完整跑完四阶段。
- 阶段失败会进入可重试或 blocked 状态。
- validator 失败可以创建新的 coder attempt。
