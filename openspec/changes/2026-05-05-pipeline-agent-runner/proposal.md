## Why

- 当前 Pipeline Console 已能跑完整 UI 和状态闭环，但 sequential stages 仍由 demo handler 生成固定报告。
- 要让流水线真正有用，下一步必须让每个 stage 调用数据库中绑定的 agent，而不是只模拟阶段完成。

## Scope

- 新增 pipeline agent runner，将 `PipelineDefinition.stages[].agent_id` 解析为真实 agent。
- Sequential execution 使用现有 `llm_gateway.run_agent` 调用 stage agent。
- Stage prompt 包含当前 story/input、当前 role、attempt，以及上游 artifacts 摘要。
- Stage artifact metadata 记录 `agent_id`、`agent_name` 和 `role`，便于追踪来源。
- 增加测试覆盖 stage agent 调用、上游 artifact 传递、API sequential execution。

## Non-Goals

- 不做真实文件写入、patch apply 或 git diff 管理。
- 不做 validator 执行 `pytest` / `npm build`。
- 不做后台队列、并发执行或长任务取消。
- 不改变现有 workflow runner。

## Acceptance Criteria

- Sequential pipeline 执行时，每个 stage SHALL 调用该 stage definition 绑定的 agent。
- 当前 story 和上游 artifact 内容 SHALL 进入 stage agent 输入。
- 生成的 stage artifact SHALL 标记真实 agent 来源。
- agent 缺失或调用异常时，pipeline run SHALL 进入 blocked。
