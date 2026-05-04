# Settings Bridge Split

## Why
- `backend/app/settings_bridge.py` 同时负责 bootstrap、`.env` 读写、structured settings 规范化和写回，职责太多。
- 这次拆分的目标是把环境文件处理和 structured settings 逻辑提到独立模块，降低维护成本，但不改变 `/api/settings` 行为。
- 现有 settings API 测试已经能覆盖外部行为，适合做行为不变的内部重组。

## Scope
- 抽出 `.env` 读写与 bootstrap helper 到 `backend/app/settings_env.py`。
- 抽出 structured settings 的默认值、规范化和写回逻辑到 `backend/app/settings_structured.py`。
- 保持现有 settings API 的输入输出、文件格式和环境变量副作用不变。

## Non-Goals
- 不修改 `/api/settings` 的请求/响应结构。
- 不调整现有 model profile 或 env var 的语义。
- 不扩展为新的 settings 功能。

## Acceptance Criteria
- `settings_bridge.py` 仍可正常导入并保持现有行为。
- `backend/tests/test_settings_api.py` 继续通过。
- 新增的 helper 测试可以直接验证 env 文件和 structured settings 逻辑。
