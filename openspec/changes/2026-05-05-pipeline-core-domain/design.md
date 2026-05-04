# Pipeline Core Domain Design

## 目标
- 为 `ai_coding` 内化建立新的 `pipeline` 领域。
- 让数据库成为 PRD、Story、阶段状态、重试和 artifact 的真相源。
- 保持现有 `workflow` 域不变。

## 数据模型
- `pipeline_definitions`
  - `id`
  - `name`
  - `kind`
  - `description`
  - `created_at`
  - `updated_at`
- `pipeline_stage_definitions`
  - `id`
  - `pipeline_id`
  - `name`
  - `role`
  - `agent_id`
  - `stage_order`
  - `retry_limit`
- `pipeline_runs`
  - `id`
  - `pipeline_id`
  - `title`
  - `source_prd_id`
  - `status`
  - `current_stage_id`
  - `input_payload`
  - `created_at`
  - `updated_at`
- `pipeline_stage_runs`
  - `id`
  - `pipeline_run_id`
  - `stage_definition_id`
  - `status`
  - `attempt`
  - `input_payload`
  - `output_payload`
  - `error_message`
  - `started_at`
  - `completed_at`
- `pipeline_artifacts`
  - `id`
  - `pipeline_run_id`
  - `stage_run_id`
  - `artifact_type`
  - `name`
  - `content`
  - `metadata`
  - `created_at`

## API 边界
- `GET /api/pipelines`
- `POST /api/pipelines`
- `GET /api/pipelines/{pipeline_id}`
- `POST /api/pipelines/{pipeline_id}/runs`
- `GET /api/pipelines/runs/{run_id}`

## 状态边界
- `pipeline_runs.status`: `pending`、`running`、`done`、`blocked`、`failed`
- `pipeline_stage_runs.status`: `pending`、`running`、`completed`、`failed`、`blocked`
- 第一阶段只提供持久化和状态读取，不自动推进阶段。

## 验证
- `backend/tests/test_pipeline_schema.py`
- `backend/tests/test_pipeline_store.py`
- `backend/tests/test_pipeline_api.py`
- 完整后端测试继续通过。
