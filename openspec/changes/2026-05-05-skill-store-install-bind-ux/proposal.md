## Why

- `Agents` 卡片上的 `Install Skills` 容易被理解成“查看技能列表”，但实际动作是打开技能仓库并把技能安装后绑定到当前 agent。
- 当前 runtime 预检只突出单一缺失项，像 `search` 这种 skill 会掩盖更关键的缺失信息，例如环境变量和 auto-provision 失败原因。

## Scope

- 将 agent 卡片入口文案改为更明确的“打开技能仓库/安装并绑定”语义。
- 在技能仓库弹窗里明确说明安装动作会同时影响 workspace 与当前 agent 绑定。
- 让 runtime 预检摘要同时展示缺失环境变量、缺失 shell 依赖和 auto-provision 错误。

## Non-Goals

- 不改变技能安装后端流程。
- 不改 skill package 的实际运行逻辑。
- 不解决 `search` 技能自身的外部 API key 缺失问题。

## Acceptance Criteria

- 用户从 Agent 卡片进入技能仓库时，能明确知道这是“安装并绑定”而不是纯浏览。
- `search` 这类 skill 的预检提示能同时看到 `TAVILY_API_KEY`、`jq` 和 auto-provision 错误。
- UI 不改变现有技能安装与 Agent 绑定的数据模型。
