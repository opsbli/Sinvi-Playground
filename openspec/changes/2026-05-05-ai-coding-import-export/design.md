# AI Coding Import Export Design

## 目标
- 支持旧 `ai_coding/worker` 文件结构与新 pipeline 数据模型之间的迁移。
- 以 pipeline database 作为真相源，同时保留导出回旧 story bundle 的能力。

## 导入映射
- `worker/shared/prd.md` -> `prd` artifact。
- `worker/stories/<story-id>/story.md` -> pipeline run `input_payload.story` 和 `story` artifact。
- `worker/stories/<story-id>/status.json` -> pipeline run metadata，不作为执行状态真相源。
- `design-v1.md` / `design-v2.md` -> `design` artifact。
- `design-review-report.md` -> `design_review` artifact。
- `implementation.md` -> `implementation` artifact。
- `test-report.md` -> `validation_report` artifact。

## 导出映射
- pipeline run `input_payload.story` 或 `story` artifact -> `story.md`。
- `prd` artifact -> `shared/prd.md`。
- stage artifacts -> 对应 legacy 文件。
- pipeline run status -> `status.json`。

## 边界
- 不读取 `worker_state.json` 作为运行状态。
- 不调用旧 `worker.py`。
- 不要求迁移全部历史目录；导入函数按一个 story bundle 执行。
