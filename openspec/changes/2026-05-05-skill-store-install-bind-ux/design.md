## Context

`Agents` 页面里的技能仓库弹窗同时承担“安装 skill 包”和“绑定 skill 到当前 agent”两种行为，但现有文案没有把这层语义表达出来。与此同时，runtime 预检当前只强调单条状态，导致像 `search` 这类 skill 的 `TAVILY_API_KEY`、`jq` 缺失以及 auto-provision 失败不会在同一处完整呈现。

## UI Design Decisions

- Agent 卡片入口改成更明确的 `Open Skill Store`，减少用户把它理解成纯浏览入口的概率。
- 技能仓库顶部增加一个目标说明区，明确当前选择的 agent 名称以及“install + bind”的动作含义。
- 技能卡片上的主按钮改成 `Install & Bind Skill`，卸载按钮改成 `Uninstall from Agent`，把动作对象说清楚。
- runtime chip 允许同时显示多个缺失原因，不再只展示第一条问题。
- 继续沿用现有 modal、glass panel、chip 和 button 视觉语言，不引入新布局或新导航。

## Data Flow Decisions

- 前端继续使用现有 `skill.runtime_preflight` 数据，不新增后端字段。
- runtime 摘要从数组字段组合生成：
  - `missing_env_vars`
  - `missing_shell_dependencies`
  - `auto_provision_errors`
  - `missing_launchers`
  - `node_prepare_required`
  - `python_prepare_required`
- 安装动作仍然是“先安装 skill 包，再更新 agent.skill_ids 绑定关系”，只改文案和状态展示，不改数据模型。

## Non-Goals

- 不修改 skill 安装 API。
- 不修改 runtime 预检逻辑本身。
- 不新增技能详情页或分步安装向导。
