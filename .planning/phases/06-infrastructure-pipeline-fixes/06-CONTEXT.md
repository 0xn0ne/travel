# Phase 6: Infrastructure & Pipeline Fixes - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix technical foundations that are broken or incomplete: Alembic migrations, Amap cache injection, Test Runner import/engine bugs, JWT production guard, seed script lat/lng bug, and auto-seed on fresh deploy. This phase does NOT add new features — it makes existing infrastructure solid and production-ready.

Requirements: INFRA-01, INFRA-02, INFRA-03, PIPE-02, PIPE-04

</domain>

<decisions>
## Implementation Decisions

### Alembic Setup (INFRA-01)
- **D-01:** Alembic configuration lives at project root (`alembic.ini` + `alembic/` directory)
- **D-02:** Migration `env.py` targets `backend.models.database` as the metadata source (`target_metadata = Base.metadata`)
- **D-03:** Initial migration auto-generated via `alembic revision --autogenerate -m "initial"` from current 7-table schema (POI, Scenario, ItineraryRow, TestResult, User, AmapCache, FeedbackLog)
- **D-04:** DB init strategy: FastAPI lifespan runs `alembic upgrade head` instead of `create_all()` — Alembic owns schema management going forward
- **D-05:** Existing `data/travel.db` is deleted and recreated from scratch via Alembic migrations — clean start, no data preservation needed

### Cache Injection (PIPE-02)
- **D-06:** `get_amap_service()` becomes request-scoped — remove `@lru_cache`, accept `db: AsyncSession = Depends(get_db)` parameter
- **D-07:** Each request gets its own `AmapService` instance with a DB session for cache lookups/stores
- **D-08:** Cache TTLs stay as currently designed: 30 days for walking routes, 7 days for POI searches
- **D-09:** `AmapService.__init__` already accepts `db_session: AsyncSession | None` — just need to pass it from the dependency

### Test Runner Fix (PIPE-04)
- **D-10:** Fix import paths: `from config import get_settings` → `from backend.config import get_settings`, same for `pipeline.coordinator` and `services.amap_service`
- **D-11:** Keep separate engine creation per group generation (user's choice — more isolated)
- **D-12:** Fix engine URL: do NOT strip `+aiosqlite` — use `settings.database_url` as-is
- **D-13:** The `_generate_for_group` method keeps its current structure, just with corrected imports and URL

### JWT Production Guard (INFRA-02)
- **D-14:** Add `ENVIRONMENT` variable to `config.py Settings` class (default: `"development"`)
- **D-15:** Guard runs in FastAPI lifespan startup — if `ENVIRONMENT == "production"` and `jwt_secret_key` is empty or equals the dev fallback, refuse to start with clear error message
- **D-16:** Development environment continues to work with fallback secret (no disruption)

### Seed Script Fix (INFRA-03)
- **D-17:** Fix `seed_pois.py` keyword args: `lat`/`lng` → `latitude`/`longitude` to match `POI` model fields
- **D-18:** After Alembic runs migrations, lifespan checks if POI table is empty and auto-seeds from `data/pois/` JSON files
- **D-19:** Also auto-seed scenarios from `data/scenarios/scenarios.json` if Scenario table is empty
- **D-20:** Auto-seed is idempotent — runs only on fresh DB, skipped if data exists

### Agent's Discretion
- Alembic migration file formatting and naming conventions
- Exact error message wording for JWT guard
- Logging level and format for auto-seed operations
- Whether to add a `--force-seed` CLI flag for manual re-seeding

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Database Models
- `src/backend/models/database.py` — All 7 SQLAlchemy models (POI, Scenario, ItineraryRow, TestResult, User, AmapCache, FeedbackLog)

### Infrastructure Files
- `src/backend/db/init_db.py` — Current init_db() with create_all(), AsyncSessionFactory, engine setup
- `src/backend/db/seed_pois.py` — Seed script with lat/lng bug to fix
- `src/backend/config.py` — Settings class, needs ENVIRONMENT variable added
- `src/backend/main.py` — FastAPI app with lifespan where startup guard and auto-seed live

### Service Files
- `src/backend/services/amap_service.py` — AmapService with cache methods (lines 38-41: constructor accepts db_session)
- `src/backend/services/test_runner.py` — TestRunnerService with broken imports (lines 38-44)
- `src/backend/api/dependencies.py` — get_amap_service() at line 34, needs @lru_cache removed + db param

### Auth
- `src/backend/api/auth.py` — get_jwt_secret_key() with dev fallback at line 58

### Data Files
- `data/pois/shanghai.json` — Shanghai POI data (97 entries)
- `data/scenarios/scenarios.json` — 4 test scenarios

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AmapService.__init__(api_key, db_session=None)` — already accepts optional db_session, just never passed
- `AmapService._cache_lookup()` / `_cache_store()` — cache methods already implemented, just need active db_session
- `init_db()` — already has engine/session factory setup, just needs Alembic integration
- `seed_pois.py` — seeding logic works, just keyword arg bug

### Established Patterns
- FastAPI dependency injection via `Depends()` — used for get_db, get_llm_client, etc.
- `@lru_cache` for singleton services — pattern to change for AmapService only
- Lifespan context manager in `main.py` — where startup logic lives
- AsyncSession via `get_async_session` — standard DB session pattern

### Integration Points
- `src/backend/api/routes/generate.py` — calls `get_amap_service()` dependency, will get request-scoped version
- `src/backend/api/routes/adjust.py` — same dependency usage
- `src/backend/api/routes/test_runner.py` — instantiates TestRunnerService with fixed dependencies
- `src/backend/main.py` lifespan — where Alembic upgrade + auto-seed + JWT guard all hook in

</code_context>

<specifics>
## Specific Ideas

- Alembic `env.py` needs to import `from backend.models.database import Base` and set `target_metadata = Base.metadata`
- The `alembic.ini` `sqlalchemy.url` should be overridden in `env.py` to read from `Settings.database_url` (not hardcoded in ini)
- Auto-seed logic: `await db.execute(select(func.count(POI.id)))` → if count is 0, run seed
- JWT guard error message should be actionable: "Set JWT_SECRET_KEY in .env or set ENVIRONMENT=development"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-infrastructure-pipeline-fixes*
*Context gathered: 2026-04-16*
