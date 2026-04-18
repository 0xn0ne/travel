---
phase: "06"
plan: "01"
subsystem: infrastructure
tags: [alembic, migrations, jwt, auto-seed, database]
dependency_graph:
  requires: [database models, seed data files]
  provides: [alembic migrations, JWT guard, auto-seed]
  affects: [init_db.py, main.py, config.py]
tech_stack:
  added: [alembic 1.18.4]
  patterns: [programmatic Alembic upgrade, lifespan startup sequence]
key_files:
  created:
    - alembic.ini
    - alembic/env.py
    - alembic/script.py.mako
    - alembic/versions/001_initial.py
  modified:
    - src/backend/db/init_db.py
    - src/backend/config.py
    - src/backend/main.py
decisions:
  - D1: Alembic owns schema via programmatic upgrade, Base.metadata.create_all removed
  - D2: JWT guard uses runtime check in lifespan, not middleware, for simplicity
  - D3: Auto-seed checks row count and only inserts on empty tables (idempotent)
  - D4: Migration file renamed from hash to 001_initial.py for readability
metrics:
  duration: 5m
  completed: "2026-04-16"
  tasks: 2
  files: 7
---

# Phase 06 Plan 01: Infrastructure Pipeline Fixes Summary

Alembic schema migrations with async support, JWT production guard, and auto-seed for fresh deploys.

## Changes Made

### Task 1: Alembic Migrations Setup
- Created `alembic.ini` with SQLite async connection string
- Created `alembic/env.py` with async migration support, reading DB URL from `Settings`
- Created `alembic/script.py.mako` migration template
- Generated `alembic/versions/001_initial.py` with all 7 tables: pois, scenarios, itineraries, test_results, users, amap_cache, feedback_logs (with proper indexes and foreign keys)
- Refactored `init_db.py` to use `alembic.command.upgrade` via `asyncio.to_thread()` instead of `Base.metadata.create_all`

### Task 2: JWT Guard and Auto-Seed
- Added `environment: str = "development"` to `Settings` class
- Added JWT production guard in lifespan: raises `RuntimeError` if `ENVIRONMENT=production` and `JWT_SECRET_KEY` is empty or the dev placeholder
- Added `_seed_if_empty()` function in main.py: seeds 97 POIs from shanghai.json and 4 scenarios from scenarios.json on empty database
- Lifespan startup order: JWT guard check → `init_db()` (Alembic migrations) → `_seed_if_empty()` (auto-seed) → yield

## Verification Results

- **Task 1**: All 7 tables + alembic_version created via `alembic upgrade head`
- **Task 2 ENVIRONMENT**: `Settings(environment='production')` correctly reads from env var
- **Task 2 JWT Guard**: RuntimeError raised in production mode with empty JWT_SECRET_KEY
- **Task 2 Auto-seed**: 97 POIs (all non-zero lat/lng) and 4 scenarios seeded on fresh DB

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All 8 files verified present. Both commits (2999e24, 74883ed) confirmed in git log.
