## Context

`pipeline_sequential.run_sequential_pipeline()` 已经提供 stage 状态机和 artifact 写入能力，并通过 `handlers` 注入每个 role 的执行逻辑。当前 routes 中的 `_stage_handler` 是 demo handler。最小真实化方案是在 handler 层接入 agent runtime，而不是重写状态机。

## Decisions

- 新增 `backend/app/pipeline_agent_runner.py`，负责从 `PipelineDefinition` 构建 `role -> StageHandler`。
- Handler 每次执行时通过 `agent_id` 获取 `AgentDefinition`，再调用 `llm_gateway.run_agent(agent, prompt)`。
- Prompt 明确包含：
  - pipeline run id、stage run id、role、attempt
  - story 或 brief 输入
  - upstream artifacts 的 type、name、content preview
  - 当前 stage 的输出要求
- 上游 artifact 从 `PipelineStore.get_pipeline_run()` 读取，避免修改 `StageExecutionInput` schema。
- `validator` 当前只记录 agent 输出并默认 `passed=true`；真实命令验证留给后续 `pipeline-validation-runner`。

## Failure Handling

- 缺失 stage definition、缺失 agent 或 LLM runtime 抛错时，handler 返回 `blocked=True`。
- `run_sequential_pipeline()` 已负责把 blocked handler 结果持久化为 stage blocked 和 run blocked。

## Data Safety

- 本次不写 workspace 文件，不执行 shell 命令。
- 只新增 pipeline artifacts 和 stage output metadata。
