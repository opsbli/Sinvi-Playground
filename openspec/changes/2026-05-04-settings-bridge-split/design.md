# Settings Bridge Split Design

## 目标
- 把 settings 协调层拆成更清晰的 helper 模块，减少 `settings_bridge.py` 的职责密度。
- 保持现有 bootstrap 行为、`.env` 文件格式和 `/api/settings` 的副作用一致。

## 设计决策
- `backend/app/settings_env.py` 负责 `.env` bootstrap、读取和写入，函数只接收路径和数据，不依赖 `settings_bridge`。
- `backend/app/settings_structured.py` 负责 structured settings 的默认值、规范化、active profile 解析和写回。
- `settings_bridge.py` 继续作为对外入口，只保留 `Settings` 加载和调用 helper 的薄封装。

## 行为边界
- `.env` 读写格式保持 `KEY=VALUE` 排序输出。
- 环境变量写回和 `reload_settings()` 调用顺序保持不变。
- structured settings 的默认 profile 和 active profile 选择规则保持不变。

## 验证
- 直接测试 `settings_env.py` 的读写和 bootstrap 行为。
- 直接测试 `settings_structured.py` 的规范化与写回行为。
- 再跑完整 `backend/tests`，确认 settings API 没有回归。
