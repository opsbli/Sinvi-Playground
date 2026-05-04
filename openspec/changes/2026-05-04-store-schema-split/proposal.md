# Store Schema Split

## Why
- `backend/app/store.py` 已经非常大，schema 创建、列迁移和初始化逻辑都塞在同一个文件里，后续继续治理会很难维护。
- 这次拆分只想把数据库 schema/bootstrap 相关逻辑抽出来，降低 `store.py` 的复杂度，不改变任何对外 API。
- 当前已经有 API 回归测试，适合先做一个行为不变的内部重组。

## Scope
- 抽出 store 的 schema/bootstrap 辅助函数到独立模块。
- 保持现有数据库表结构、默认列、索引和初始化顺序不变。
- 新增一个直接覆盖 schema 初始化行为的最小测试。

## Non-Goals
- 不修改 agent / workflow / conversation 的业务行为。
- 不改变 SQLite 数据模型的字段语义。
- 不做更大范围的 repository/service 分层重构。

## Acceptance Criteria
- `store.py` 仍可正常导入并对外提供相同的 `SQLitePlaygroundStore` 行为。
- schema 初始化逻辑被提取到独立模块，且测试可直接验证它。
- `pytest backend/tests -q` 继续通过。
