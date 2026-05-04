# Store Schema Split Design

## 目标
- 把 `store.py` 中和数据库表结构创建、列补齐相关的逻辑提取出来，减少单文件复杂度。
- 保留 `SQLitePlaygroundStore` 现有公开接口和初始化副作用，不改变调用方。

## 设计决策
- 新增 `backend/app/store_schema.py` 承担 schema 创建和列补齐函数。
- `store.py` 仍然负责高层 store 行为、文件技能同步、CRUD 与业务编排。
- schema helper 接收现成的 `sqlite3.Connection`，只做纯 SQL 初始化，不持有 store 状态。
- 抽出的函数以最小依赖设计，避免和 settings 或 runtime 产生新的耦合。

## 行为边界
- 表名、列名、默认值、索引名都保持不变。
- 初始化顺序保持不变，确保旧数据库继续兼容。
- 对外 API、返回 payload、错误行为不变。

## 验证
- 用一个直接操作临时 SQLite 数据库的测试验证 schema helper 能创建核心表和关键列。
- 再跑完整 `backend/tests`，确认 API 回归没变。
