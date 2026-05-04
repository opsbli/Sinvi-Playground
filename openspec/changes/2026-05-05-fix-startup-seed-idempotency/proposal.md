## Why

- 前后端启动后，`Agents` 和方案列表会出现相同默认/演示数据成倍重复，影响用户选择真实 agent 与 workflow。
- 当前启动种子逻辑缺少幂等 upsert 与历史重复数据收敛，已有非默认 agent 时也不会补齐新的默认 agents。

## Scope

- 让后端启动 `seed_defaults()` 对默认 agents 执行幂等补齐，而不是只在 agents 全空时创建。
- 对已知默认/演示 agents 与 workflows 执行保守去重，保留第一条并删除未被引用的重复 agent、重复 workflow。
- 增加回归测试覆盖重复启动、已有非默认数据、历史重复方案清理。

## Non-Goals

- 不删除未知用户自建 agents 或 workflows。
- 不重写 workflow 编排模型、agent 导入模型或前端列表逻辑。
- 不引入数据库迁移工具链。

## Acceptance Criteria

- 连续多次启动或调用 `seed_defaults()` 后，默认 agents 不重复。
- 数据库存在其他 agent 时，默认 `产品经理`、`设计师`、`工程师` 仍会被补齐。
- 已知演示方案重复时，启动后同名同类型方案只保留一份。
