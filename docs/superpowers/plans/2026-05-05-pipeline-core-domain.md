# Pipeline Core Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the persistence and API foundation for long-running pipeline runs without changing existing workflow behavior.

**Architecture:** Add a new `pipeline` domain beside the existing `workflow` domain. The first phase only creates schemas, SQLite tables, store methods, and minimal API routes; execution remains out of scope.

**Tech Stack:** FastAPI, Pydantic, SQLite, pytest.

---

## File Structure
- Create: `backend/app/pipeline_schemas.py` for pipeline-specific Pydantic models.
- Create: `backend/app/pipeline_store.py` for focused persistence helpers.
- Create: `backend/app/routes_pipelines.py` for `/api/pipelines` endpoints.
- Modify: `backend/app/store_schema.py` to create pipeline tables.
- Modify: `backend/app/routes.py` to include the pipeline router.
- Test: `backend/tests/test_pipeline_schema.py`.
- Test: `backend/tests/test_pipeline_store.py`.
- Test: `backend/tests/test_pipeline_api.py`.

## Task 1: Pipeline Schema Models

**Files:**
- Create: `backend/app/pipeline_schemas.py`
- Test: `backend/tests/test_pipeline_schema.py`

- [x] **Step 1: Write the failing schema test**

```python
from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate


def test_pipeline_definition_create_defaults():
    payload = PipelineDefinitionCreate(
        name="AI Coding",
        kind="sequential_pipeline",
        description="Story execution pipeline.",
        stages=[
            {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1}
        ],
    )

    assert payload.stages[0].retry_limit == 1


def test_pipeline_run_create_accepts_input_payload():
    payload = PipelineRunCreate(
        title="US-001",
        input_payload={"story": "Build layout"},
    )

    assert payload.input_payload["story"] == "Build layout"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_pipeline_schema.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.pipeline_schemas'`.

- [x] **Step 3: Add minimal schema implementation**

Create `backend/app/pipeline_schemas.py` with request/response models for definition, stage definition, run, stage run, and artifact.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_pipeline_schema.py -q`
Expected: PASS.

## Task 2: SQLite Tables

**Files:**
- Modify: `backend/app/store_schema.py`
- Test: `backend/tests/test_pipeline_store.py`

- [x] **Step 1: Write failing schema initialization test**

```python
import sqlite3

from app.store_schema import initialize_schema


def test_initialize_schema_creates_pipeline_tables():
    connection = sqlite3.connect(":memory:")
    initialize_schema(connection)

    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'pipeline_%'"
    ).fetchall()
    names = {row[0] for row in rows}

    assert "pipeline_definitions" in names
    assert "pipeline_stage_definitions" in names
    assert "pipeline_runs" in names
    assert "pipeline_stage_runs" in names
    assert "pipeline_artifacts" in names
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_pipeline_store.py::test_initialize_schema_creates_pipeline_tables -q`
Expected: FAIL because pipeline tables do not exist.

- [x] **Step 3: Add table creation SQL**

Add table creation statements to `initialize_schema(connection)` in `backend/app/store_schema.py`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_pipeline_store.py::test_initialize_schema_creates_pipeline_tables -q`
Expected: PASS.

## Task 3: Pipeline Store

**Files:**
- Create: `backend/app/pipeline_store.py`
- Test: `backend/tests/test_pipeline_store.py`

- [x] **Step 1: Add failing CRUD test**

```python
from pathlib import Path

from app.pipeline_schemas import PipelineDefinitionCreate, PipelineRunCreate
from app.pipeline_store import PipelineStore


def test_pipeline_store_creates_definition_and_run(tmp_path: Path):
    store = PipelineStore(tmp_path / "pipeline.db")
    definition = store.create_pipeline_definition(
        PipelineDefinitionCreate(
            name="AI Coding",
            kind="sequential_pipeline",
            description="Story execution pipeline.",
            stages=[
                {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1},
                {"name": "Review", "role": "reviewer", "agent_id": "agent_reviewer", "stage_order": 2},
            ],
        )
    )

    run = store.create_pipeline_run(
        definition.id,
        PipelineRunCreate(title="US-001", input_payload={"story": "Build layout"}),
    )
    detail = store.get_pipeline_run(run.id)

    assert detail is not None
    assert detail.current_stage_id == definition.stages[0].id
    assert [stage.status for stage in detail.stage_runs] == ["pending", "pending"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_pipeline_store.py -q`
Expected: FAIL because `app.pipeline_store` does not exist.

- [x] **Step 3: Implement store**

Create `PipelineStore` with `create_pipeline_definition`, `list_pipeline_definitions`, `get_pipeline_definition`, `create_pipeline_run`, and `get_pipeline_run`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_pipeline_store.py -q`
Expected: PASS.

## Task 4: Pipeline API

**Files:**
- Create: `backend/app/routes_pipelines.py`
- Modify: `backend/app/routes.py`
- Test: `backend/tests/test_pipeline_api.py`

- [x] **Step 1: Write failing API test**

```python
def test_pipeline_api_creates_definition_and_run(api_client):
    definition_response = api_client.post(
        "/api/pipelines",
        json={
            "name": "AI Coding",
            "kind": "sequential_pipeline",
            "description": "Story execution pipeline.",
            "stages": [
                {"name": "Design", "role": "designer", "agent_id": "agent_designer", "stage_order": 1}
            ],
        },
    )
    assert definition_response.status_code == 200
    definition = definition_response.json()

    run_response = api_client.post(
        f"/api/pipelines/{definition['id']}/runs",
        json={"title": "US-001", "input_payload": {"story": "Build layout"}},
    )
    assert run_response.status_code == 200
    assert run_response.json()["current_stage_id"] == definition["stages"][0]["id"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_pipeline_api.py -q`
Expected: FAIL with 404 for `/api/pipelines`.

- [x] **Step 3: Implement route module and include router**

Create `routes_pipelines.py` using `PipelineStore(store.db_path)` or an equivalent shared instance, then include it from `routes.py`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_pipeline_api.py -q`
Expected: PASS.

## Task 5: Full Verification

**Files:**
- No new files.

- [x] **Step 1: Run full backend tests**

Run: `python -m pytest backend/tests -q`
Expected: all tests pass.

- [x] **Step 2: Review OpenSpec artifacts**

Read:
- `openspec/changes/2026-05-05-pipeline-core-domain/proposal.md`
- `openspec/changes/2026-05-05-pipeline-core-domain/design.md`
- `openspec/changes/2026-05-05-pipeline-core-domain/tasks.md`

Expected: implementation scope matches artifacts; no runner, PRD generation, import/export, or UI work is included.

- [x] **Step 3: Commit**

```bash
git add backend/app/pipeline_schemas.py backend/app/pipeline_store.py backend/app/routes_pipelines.py backend/app/routes.py backend/app/store_schema.py backend/tests/test_pipeline_schema.py backend/tests/test_pipeline_store.py backend/tests/test_pipeline_api.py openspec/changes/2026-05-05-pipeline-core-domain docs/superpowers/plans/2026-05-05-pipeline-core-domain.md
git commit -m "feat: add pipeline core domain"
```

## Follow-Up Plans
- `2026-05-05-ai-coding-agent-import`
- `2026-05-05-pipeline-prd-story-generation`
- `2026-05-05-pipeline-sequential-execution`
- `2026-05-05-ai-coding-import-export`

