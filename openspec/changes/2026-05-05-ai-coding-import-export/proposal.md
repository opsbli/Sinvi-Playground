# AI Coding Import Export

## Why
- 旧 `ai_coding/worker` 的文件数据需要可迁移到新 pipeline。
- 内化初期需要保留导入/导出能力，方便回退和对照。

## Scope
- 导入 `worker/shared/prd.md`。
- 导入 `worker/stories/*/story.md`、`status.json` 和阶段产物。
- 导出 pipeline run 为旧 worker story bundle。

## Non-Goals
- 不使用旧 `worker_state.json` 作为运行真相源。
- 不继续调用旧 `worker.py`。
- 不要求一次性迁移所有历史数据。

## Acceptance Criteria
- 一个旧 story 文件夹可以导入为 pipeline run。
- 一个 pipeline run 可以导出为兼容旧 worker 的文件结构。
- 导入/导出结果可重复验证。
