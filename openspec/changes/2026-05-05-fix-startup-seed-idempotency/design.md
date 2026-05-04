## Context

启动入口 `backend/app/main.py` 会调用 `store.seed_defaults()`。该方法承担默认 agents 初始化、legacy agent rename、skill 文件迁移等职责。重复问题发生在持久化 SQLite 数据库中，因此修复必须在 store 层保证幂等，而不是依赖前端过滤。

## Decisions

- `seed_defaults()` 使用按 name 的 upsert 语义补齐默认 agents：如果目标默认 agent 不存在就创建；如果存在就只补齐缺失的 skill ids，不覆盖用户可能调整过的 prompt、model 或 capabilities。
- 已知演示 workflows 按 `(name, type)` 去重，保留最早创建的一条，删除后续重复项，并复用现有 `delete_workflow()` 清理关联 conversations 和 messages。
- 已知默认/演示 agents 去重时只删除未被任何保留 workflow 引用的重复 agent，避免破坏仍可用的用户方案。
- 清理范围使用 allowlist，避免误删用户自建数据。

## Data Safety

- 去重只覆盖项目曾经自动生成或演示使用的固定名称。
- 未知名称、未知 workflow type、或仍被 workflow 引用的重复 agent 不会被删除。
- 实际数据修复通过同一个 `seed_defaults()` 执行，保证启动路径和手动修复路径一致。
