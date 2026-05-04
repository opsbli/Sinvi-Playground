# Tasks

- [x] 为 agent 增加最小来源元数据存储，或新增 agent metadata 表。
- [x] 新增 `backend/app/seeds/ai_coding_agents.py`，读取 `ai_coding/worker/agents/*.md`。
- [x] 实现幂等 upsert，按 `pipeline_family + role` 定位 agent。
- [x] 增加导入测试，覆盖首次导入和重复导入。
- [x] 运行 `python -m pytest backend/tests -q` 并确认通过。
