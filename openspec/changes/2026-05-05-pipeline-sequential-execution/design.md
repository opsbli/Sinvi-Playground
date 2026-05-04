# Pipeline Sequential Execution Design

## 目标
- 在 pipeline core 之上提供 `designer -> reviewer -> coder -> validator` 顺序状态机。
- 把每个 stage 的 input、output、artifact、trace、attempt 和错误写回数据库。
- 支持 validator 失败后回到 coder，创建新的 coder attempt。

## 执行模型
- `run_sequential_pipeline(store, run_id, handlers)` 从当前 run 的 stage run 状态开始执行。
- 每个 handler 接收 `StageExecutionInput`，返回 `StageExecutionResult`。
- runner 不直接调用 LLM；handler 是可注入执行边界，后续 change 可接真实 agent runtime。
- 本阶段固定支持 `designer`、`reviewer`、`coder`、`validator` 四个角色。

## 状态规则
- stage run 开始时置为 `running`，写入 input payload 和 attempt。
- handler 成功时置为 `completed`，写入 output payload，并按阶段产出 artifact。
- handler 抛错或返回 blocked 时，该 stage 置为 `blocked`，pipeline run 置为 `blocked`。
- 全部阶段完成后 pipeline run 置为 `done`。
- validator 返回 `passed=False` 时，validator stage 置为 `failed`，创建一个新的 coder stage run，attempt +1，并把 run 的 current stage 指回 coder。

## Artifact 映射
- designer -> `design`
- reviewer -> `design_review`
- coder -> `implementation`
- validator -> `validation_report`

## Non-Goals
- 不调用真实 LLM。
- 不实现 UI。
- 不执行旧 `worker.py`。
