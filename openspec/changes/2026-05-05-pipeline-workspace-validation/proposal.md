## Why

- Pipeline stage 现在已经能调用真实 agent，但 coder 输出仍只是 artifact 文本，不会形成可检查的 workspace 文件。
- Validator 也还没有执行任何验证命令，因此流水线无法证明产物是否可用。

## Scope

- 为 pipeline run 创建受控 workspace：`<db-dir>/pipeline-workspaces/<run-id>/`。
- coder stage 支持从 agent 输出中提取 `pipeline-file` fenced blocks，并写入 workspace。
- 记录 workspace manifest artifact，包含 workspace 路径与生成文件列表。
- validator stage 支持执行 `input_payload.validation_commands` 中的 argv 命令，cwd 固定为 run workspace。
- 记录 validation command artifact，包含 command、exit code、stdout、stderr 和 timeout 状态。

## Non-Goals

- 不执行任意 shell 字符串，不支持 `shell=True`。
- 不做 git patch、branch、commit 或 PR。
- 不做后台队列或长任务取消。
- 不做前端编辑器；现有 artifact 面板继续展示 manifest 和 validation report。

## Acceptance Criteria

- coder 输出合法 `pipeline-file` block 时，系统 SHALL 在 run workspace 写入对应文件。
- coder 试图写绝对路径或 `..` 越界路径时，stage SHALL blocked。
- validator SHALL 执行配置的 argv validation commands，并把结果写入 artifact。
- validation command 非零退出码 SHALL 让 validator output `passed=false`，触发既有 retry 逻辑。
