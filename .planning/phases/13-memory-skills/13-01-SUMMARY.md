# Plan 13-01: AgentMemory Model + Memory Tools

**Status:** Complete
**Commits:**
- `c12745b` feat(13-01): add AgentMemory model and Alembic migration
- `a854a7d` feat(13-01): add memory read/write tools and cleanup service

## What Was Done

### Task 1: AgentMemory Model + Alembic Migration

**File: `src/backend/models/database.py`**
- Added `ALLOWED_CATEGORIES = {"preference", "constraint", "feedback", "trip_context"}` constant
- Added `AgentMemory` SQLAlchemy model with 9 columns:
  - `id` (UUID String(36), PK)
  - `user_id` (FK to users.id, indexed)
  - `key` (String(200), indexed)
  - `value` (Text, JSON-serialized dict)
  - `category` (String(50), validated)
  - `access_count` (Integer, default=1)
  - `created_at`, `updated_at`, `last_accessed_at` (DateTime, default=_utcnow)
- Added `@validates("category")` enforcing the 4 allowed categories
- Added composite index `ix_agent_memories_user_category` on `(user_id, category)`

**File: `alembic/versions/a422b22ab4c1_add_agent_memories_table.py`**
- Migration creates `agent_memories` table with FK to `users.id`
- Creates 3 indexes: `ix_agent_memories_user_id`, `ix_agent_memories_key`, `ix_agent_memories_user_category`
- Verified: `alembic upgrade head` runs cleanly on existing DB

### Task 2: Memory Tools + Cleanup Service

**File: `src/backend/tools/memory.py`**
- `write_memory(ctx, key, value, category)`: validates category, parses JSON value (requires `note` field), upserts by `user_id+key`, rejects anonymous users
- `read_memories(ctx, category=None, limit=20)`: returns `[]` for anonymous, profile-scored retrieval using `taste_tags` overlap for authenticated users, recency fallback for new users

**File: `src/backend/services/memory_cleanup.py`**
- `cleanup_memories(db_session)`: quarterly cleanup with 3 steps:
  1. Delete `trip_context` memories older than 7 days
  2. Delete pre-quarter memories with `access_count <= 3`
  3. Delete bottom 20% of remaining pre-quarter memories by access count
- CLI entry point: `python -m backend.services.memory_cleanup`

**File: `src/backend/tools/__init__.py`**
- Added `read_memories` and `write_memory` to `ALL_TOOLS` (12 tools total)
- Fixed pre-existing bug: `itinerary_context` → `get_itinerary_context`

## Verification Results

All verification commands passed:
- `ALLOWED_CATEGORIES == {'preference', 'constraint', 'feedback', 'trip_context'}` ✓
- `alembic upgrade head` creates agent_memories table ✓
- `init_db()` runs without error ✓
- `from backend.tools.memory import read_memories, write_memory` ✓
- `from backend.services.memory_cleanup import cleanup_memories` ✓
- `ALL_TOOLS` has 12 tools with both memory tools ✓

## Notes

- The `alembic/` directory is gitignored — migration file exists on disk but is not tracked in git (consistent with existing migration `9ccde6d944e6`)
- The initial migration was stamped manually with `alembic stamp head` before generating the new migration
