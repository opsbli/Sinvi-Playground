# Workflows Route Split Plan

## Goal
把 `backend/app/routes.py` 里的 workflows 相关 HTTP 端点抽出来，减少主路由文件体积，同时保持 `/api/workflows` 和 `/api/workflows/{workflow_id}/graph` 行为不变。

## Steps
1. 先补一个直接覆盖 workflows 路由 helper 的测试，锁定创建校验和 graph dispatch。
2. 把 workflows CRUD 和 graph 端点提取到 `backend/app/routes_workflows.py`，并让 `routes.py` 只做 router include。
3. 跑完整后端测试，确认没有回归。

## Status
Completed.

## Verification
- `python -m pytest backend/tests/test_workflow_routes.py -q`
- `python -m pytest backend/tests -q`
