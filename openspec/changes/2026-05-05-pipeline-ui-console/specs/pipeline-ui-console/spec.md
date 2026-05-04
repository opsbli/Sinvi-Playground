## ADDED Requirements

### Requirement: Pipeline Console Navigation

前端 SHALL 提供独立的 `Pipelines` 导航入口，用于查看和操作 pipeline definitions 与 runs。

#### Scenario: User opens pipeline console

- GIVEN 用户打开应用
- WHEN 用户点击 `Pipelines`
- THEN 页面 SHALL 显示 pipeline definitions、brief 输入区、story queue 和 run detail 区

### Requirement: AI Coding Bootstrap

系统 SHALL 支持从界面触发 AI Coding pipeline bootstrap，并保持幂等。

#### Scenario: Bootstrap creates reusable definitions

- GIVEN 数据库中不存在 AI Coding pipeline definitions
- WHEN 用户触发 bootstrap
- THEN 系统 SHALL 创建 `PRD Story Generation` 和 `AI Coding Sequential`
- AND 再次触发 bootstrap SHALL 不创建重复 definitions

### Requirement: PRD Story Generation From UI

系统 SHALL 支持从 brief 生成 PRD 与 Story artifacts。

#### Scenario: Generate stories from brief

- GIVEN 用户已完成 pipeline bootstrap
- WHEN 用户输入 brief 并触发生成
- THEN 系统 SHALL 创建一个 PRD/story pipeline run
- AND run artifacts SHALL 包含一个 `prd` artifact 和至少一个 `story` artifact

### Requirement: Sequential Story Run From UI

系统 SHALL 支持从 Story artifact 创建并执行 sequential pipeline run。

#### Scenario: Execute story run

- GIVEN 用户已有一个 `story` artifact
- WHEN 用户选择该 story 并触发 run
- THEN 系统 SHALL 创建 sequential pipeline run
- AND sequential execution SHALL 更新 stage statuses
- AND 页面 SHALL 显示 stage statuses 与 generated artifacts
