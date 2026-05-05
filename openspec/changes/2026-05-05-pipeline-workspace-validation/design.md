## Context

`pipeline_agent_runner` 已负责把 stage agent 接入 sequential runner。Workspace 与 validation 能力应继续放在 handler 层，因为它们是 stage execution 的副作用，不需要改变 pipeline 状态机。

## Decisions

- 新增 `pipeline_workspace_executor.py`：
  - `workspace_root_for_run()` 计算每个 run 的 workspace。
  - `materialize_pipeline_files()` 只解析 fenced block：````pipeline-file path="relative/path"`。
  - 写入前解析并校验路径必须留在 workspace 内。
- 新增 `pipeline_validation_runner.py`：
  - 只接受 `validation_commands` 里的 `list[list[str]]`。
  - 使用 `subprocess.run(..., shell=False, cwd=workspace, timeout=...)`。
  - 默认 timeout 30 秒，可通过 `validation_timeout_seconds` 覆盖。
- `pipeline_agent_runner` 在 coder stage 后调用 workspace executor，在 validator stage 后调用 validation runner。
- Validation result 会合并到 validator content，并通过 `output_payload.passed` 控制既有 retry 逻辑。

## Safety

- 不支持 shell 字符串，避免 `&&`、重定向、管道等未审计行为。
- 不允许绝对路径和 `..` 越界路径。
- validation cwd 固定在 run workspace，不在 repo root 或用户任意目录执行。
