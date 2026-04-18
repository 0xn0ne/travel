---
phase: 06
plan: 02
subsystem: infrastructure
tags: [amap-service, db-session, caching, test-runner, import-fix]
dependency_graph:
  requires: [06-01]
  provides: [request-scoped-amap-service, working-test-runner]
  affects: [dependencies.py, test_runner.py]
tech_stack:
  added: []
  patterns: [request-scoped-dependency, db-session-injection]
key_files:
  created: []
  modified:
    - src/backend/api/dependencies.py
    - src/backend/services/test_runner.py
decisions:
  - AmapService made request-scoped (not singleton) so DB-backed cache uses the request's DB session
  - Test runner uses settings.database_url directly — SQLAlchemy handles +aiosqlite dialect correctly
metrics:
  duration: 2m
  completed: 2026-04-16
---

# Phase 6 Plan 02: AmapService Cache + Test Runner Fix Summary

Made AmapService request-scoped with DB session injection for caching, and fixed Test Runner import paths to generate A/B/C itineraries correctly.

## Changes Made

### Task 1: AmapService Request-Scoped Dependency

**File:** `src/backend/api/dependencies.py`

- Removed `@lru_cache` decorator from `get_amap_service()` (was a singleton — now creates per-request)
- Added `db: AsyncSession = Depends(get_db)` parameter for request-scoped DB session
- Passes `db_session=db` to `AmapService` constructor so DB-backed cache works correctly

### Task 2: Test Runner Import Paths + Engine URL

**File:** `src/backend/services/test_runner.py`

- Fixed 3 import paths: `config` → `backend.config`, `pipeline.coordinator` → `backend.pipeline.coordinator`, `services.amap_service` → `backend.services.amap_service`
- Fixed engine URL: removed `.replace("+aiosqlite", "")` — SQLAlchemy handles the dialect correctly
- Passes `db_session=sess` to `AmapService` constructor for DB-backed caching

## Verification Results

All three verification commands passed:

1. **Task 1 verify:** `get_amap_service params = ['db'], no lru_cache` ✅
2. **Task 2 verify:** All `backend.*` imports resolve, no `+aiosqlite` stripping ✅
3. **End-to-end:** `TestRunnerService` imports resolve end-to-end ✅

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None.
