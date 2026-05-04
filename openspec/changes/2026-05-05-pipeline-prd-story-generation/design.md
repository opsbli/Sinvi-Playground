# Pipeline PRD Story Generation Design

## 目标
- 把 `brief -> PRD -> Stories` 内化为 pipeline 上游能力。
- 让 PRD 和 Story 作为 `pipeline_artifacts` 持久化，供后续顺序执行阶段读取。
- 本阶段提供 deterministic runner，避免在基础数据流尚未稳定时引入 LLM runtime 变量。

## 数据与 artifact
- `PRD artifact`
  - `artifact_type`: `prd`
  - `name`: `PRD`
  - `content`: Markdown PRD 正文
  - `metadata`: 包含 `brief`
- `Story artifact`
  - `artifact_type`: `story`
  - `name`: Story id，例如 `US-001`
  - `content`: Markdown Story 正文
  - `metadata`: 包含 `story_id`、`title`、`source_prd_artifact_id`

## Runner 边界
- `generate_prd_from_brief(brief)` 负责生成最小可用 PRD 文档。
- `split_prd_into_stories(prd_content)` 负责生成可执行 Story artifact payload。
- `run_prd_story_generation(store, pipeline_id, brief)` 负责创建 pipeline run、写入 PRD artifact、写入 Story artifacts。
- 本阶段不调用 LLM，不执行 designer/reviewer/coder/validator。

## Agent Seed
- 新增 `prd_writer` agent seed，描述 PRD 生成职责。
- 新增 `story_splitter` agent seed，描述 Story 拆分职责。
- 使用已有 `agent_import_metadata` 的 `pipeline_family + role` 幂等定位。

## 风险与限制
- deterministic runner 只生成结构化初稿，不替代真实产品分析。
- Story 拆分策略以 Markdown 章节和 bullet 为主，后续可替换为 LLM runner。
