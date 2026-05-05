## ADDED Requirements

### Requirement: Clear Skill Store Entry

前端 SHALL 将 Agent 卡片上的技能仓库入口标识为打开技能仓库，而不是纯浏览或单独安装按钮。

#### Scenario: User opens the skill store from an agent card

- GIVEN 用户在 Agents 页面查看某个 agent
- WHEN 用户点击技能仓库入口
- THEN 页面 SHALL 打开与该 agent 关联的技能仓库弹窗
- AND 弹窗 SHALL 明确显示当前目标 agent

### Requirement: Install And Bind Semantics

技能仓库 SHALL 将安装动作表述为安装并绑定到当前 agent。

#### Scenario: User installs a skill from the store

- GIVEN 用户已打开某个 agent 的技能仓库
- WHEN 用户点击 skill 的主操作按钮
- THEN 界面 SHALL 明确表述这是安装并绑定 skill
- AND 已安装 skill 的主操作 SHALL 表述为从当前 agent 卸载

### Requirement: Multi-Reason Runtime Summary

技能仓库 SHALL 在卡片上同时展示 skill runtime 预检的多个缺失原因。

#### Scenario: Search skill is missing env vars and dependencies

- GIVEN `search` skill 的 runtime 预检同时存在缺失环境变量、缺失 shell 依赖和 auto-provision 错误
- WHEN 用户查看该 skill 的 runtime chip
- THEN 页面 SHALL 同时展示 `TAVILY_API_KEY`
- AND 页面 SHALL 同时展示 `jq`
- AND 页面 SHALL 同时展示 auto-provision 错误摘要
- AND 页面 SHALL 不只显示单一缺失项
