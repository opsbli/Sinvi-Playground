# Settings Route Split Plan

## Goal
把 `backend/app/routes.py` 里的 settings 端点抽出来，继续缩小主路由文件体积，同时保持 `/api/settings` 行为不变。

## Steps
1. 先补一个直接覆盖 settings 路由 helper 的测试，锁定 normalized payload 读取和更新行为。
2. 把 settings GET/PUT 端点提取到 `backend/app/routes_settings.py`，并让 `routes.py` 只做 router include。
3. 跑完整后端测试，确认没有回归。

## Status
Completed.

## Verification
- `python -m pytest backend/tests/test_settings_routes.py -q`
- `python -m pytest backend/tests -q`
