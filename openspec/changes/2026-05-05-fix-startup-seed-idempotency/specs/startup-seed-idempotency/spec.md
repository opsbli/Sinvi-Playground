## ADDED Requirements

### Requirement: Startup Seed Idempotency

后端启动默认种子逻辑 SHALL 对默认 agents 和已知演示 workflows 保持幂等。

#### Scenario: Default agents are backfilled when other agents exist

- GIVEN 数据库中已经存在至少一个非默认 agent
- WHEN 后端调用 `seed_defaults()`
- THEN `产品经理`、`设计师`、`工程师` SHALL 各存在一条
- AND 非默认 agent SHALL 保留

#### Scenario: Repeated startup does not duplicate default agents

- GIVEN 数据库已经执行过一次 `seed_defaults()`
- WHEN 再次调用 `seed_defaults()`
- THEN `产品经理`、`设计师`、`工程师` SHALL 仍各只有一条

#### Scenario: Known duplicated demo workflows are collapsed

- GIVEN 数据库存在多个同名同类型的已知演示 workflow
- WHEN 后端调用 `seed_defaults()`
- THEN 每个已知演示 `(name, type)` 组合 SHALL 最多保留一条 workflow
- AND 未知用户自建 workflow SHALL 不被删除
