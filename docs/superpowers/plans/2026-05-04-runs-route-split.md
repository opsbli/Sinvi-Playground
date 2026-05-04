# Runs Route Split Plan

## Goal
把 `backend/app/routes.py` 里的 runs 与 streaming 逻辑抽出来，继续缩小主路由文件体积，同时保持 `/api/runs` 和 `/api/runs/stream` 行为不变。

## Steps
1. 先补一个直接覆盖 runs 路由 helper 的测试，锁定 dispatch 和 conversation 写入行为。
2. 把 runs 与 streaming 端点提取到 `backend/app/routes_runs.py`，并让 `routes.py` 只做 router include。
3. 跑完整后端测试，确认没有回归。

## Status
Completed.

## Verification
- `python -m pytest backend/tests/test_run_routes.py -q`
- `python -m pytest backend/tests -q`
