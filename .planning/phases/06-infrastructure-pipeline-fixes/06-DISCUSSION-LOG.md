# Phase 6: Infrastructure & Pipeline Fixes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 06-infrastructure-pipeline-fixes
**Areas discussed:** Alembic setup, Cache injection, Test Runner fix, JWT production guard, Seed script, DB init strategy, Existing DB handling

---

## Alembic Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Root-level Alembic | alembic.ini at project root, migration env targets backend.models.database | ✓ |
| Backend-embedded Alembic | Inside src/backend/, closer to models | |
| You decide | Simplest approach | |

**User's choice:** Root-level Alembic
**Notes:** Standard for Docker deployment. Migration env targets backend.models.database.

### Initial Migration

| Option | Description | Selected |
|--------|-------------|----------|
| Autogenerate migration | `alembic revision --autogenerate` from current 7-table schema | ✓ |
| Manual initial migration | Write by hand reflecting current schema | |

**User's choice:** Autogenerate migration
**Notes:** Handles future schema changes cleanly.

---

## Cache Injection

| Option | Description | Selected |
|--------|-------------|----------|
| Request-scoped service | Remove @lru_cache, pass db: AsyncSession via Depends() | ✓ |
| Singleton + per-call session | Keep singleton, pass session per cache call | |

**User's choice:** Request-scoped service
**Notes:** Each request gets its own AmapService with DB session. Cleaner dependency injection.

### Cache TTL

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing TTLs | 30d walking routes, 7d POI searches | ✓ |
| Shorter TTLs | 7d routes, 3d POI searches | |

**User's choice:** Keep existing TTLs
**Notes:** Current design matches production needs.

---

## Test Runner Fix

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse AsyncSessionFactory | Fix imports + share connection pool | |
| Fix imports only | Keep separate engine, more isolated | ✓ |

**User's choice:** Fix imports only (keep separate engine)
**Notes:** User prefers isolation over connection sharing.

### Engine URL

| Option | Description | Selected |
|--------|-------------|----------|
| Keep separate engine, fix URL | Don't strip +aiosqlite from database_url | ✓ |
| Reuse factory | Use AsyncSessionFactory for session | |

**User's choice:** Keep separate engine, fix URL
**Notes:** Fix the URL to keep `+aiosqlite` driver. Fix imports to use `backend.` prefix.

---

## JWT Production Guard

| Option | Description | Selected |
|--------|-------------|----------|
| Startup guard | Check in FastAPI lifespan, refuse to start if production + empty JWT key | ✓ |
| Config validator | Check in pydantic Settings validator | |

**User's choice:** Startup guard
**Notes:** Add ENVIRONMENT variable to config.py (default: development). Guard in lifespan.

### Environment Detection

| Option | Description | Selected |
|--------|-------------|----------|
| ENVIRONMENT env var | Add to config.py, check if "production" in lifespan | ✓ |
| Docker marker detection | Check for /.dockerenv or DEBUG=False | |

**User's choice:** ENVIRONMENT env var
**Notes:** Explicit opt-in via environment variable.

---

## Seed Script

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-seed on startup | Detect empty POI table, run seed automatically | ✓ |
| Manual seed only | Document in README, run script manually | |

**User's choice:** Auto-seed on startup
**Notes:** Zero manual steps for fresh deploy.

---

## DB Init Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Alembic-first | Lifespan runs `alembic upgrade head`, then auto-seed if empty | ✓ |
| Dual mode | Keep create_all() as fallback if Alembic not configured | |

**User's choice:** Alembic-first
**Notes:** Alembic owns schema management. No more create_all().

---

## Existing DB Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve + stamp | Alembic stamp head on existing DB | |
| Clean start | Delete existing DB, let Alembic recreate | ✓ |

**User's choice:** Clean start
**Notes:** Existing travel.db deleted and recreated from Alembic migrations.

---

## Agent's Discretion

- Alembic migration file formatting and naming conventions
- Exact error message wording for JWT guard
- Logging level and format for auto-seed operations
- Whether to add a `--force-seed` CLI flag for manual re-seeding

## Deferred Ideas

None — discussion stayed within phase scope.
