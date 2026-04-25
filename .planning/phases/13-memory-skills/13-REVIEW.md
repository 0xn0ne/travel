---
phase: 13-memory-skills
reviewed: 2026-04-21T12:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/backend/models/database.py
  - src/backend/tools/memory.py
  - src/backend/services/memory_cleanup.py
  - src/backend/services/skill_config.py
  - src/backend/services/skill_matcher.py
  - src/backend/api/dependencies.py
  - src/backend/agent/context.py
  - src/backend/tools/__init__.py
  - alembic/versions/a422b22ab4c1_add_agent_memories_table.py
  - tests/test_memory_skills_integration.py
  - tests/test_tools_integration.py
findings:
  critical: 2
  warning: 5
  info: 5
  total: 12
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-04-21T12:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Phase 13 adds a per-user memory store (AgentMemory model + read/write tools + quarterly cleanup) and a skill system (config loader + auto-activation matcher + 3 pre-built skills with prompt templates), wired into the SDK Agent DI pipeline.

The implementation is well-structured and follows established project patterns (Pydantic + lru_cache for config, RunContextWrapper for tools). Tests cover the main paths (21 tests, all passing). However, there are **2 critical issues** around security and data integrity, **5 warnings** around edge cases and robustness, and **5 info-level items** for code quality.

**Security:** Memory tools are properly scoped per-user via `ctx.context.user_id` and anonymous writes are correctly rejected. No cross-user data leakage in the tool layer.

**Key concerns:**
1. The quarterly cleanup has a deletion bug — it deletes more rows than intended (bottom 20% threshold overlaps with already-deleted ≤3 rows)
2. `build_skill_prompt` will raise `FileNotFoundError` at runtime if a prompt file is missing — no error handling
3. The upsert in `write_memory` has a race condition under concurrent writes
4. Tests duplicate production logic rather than testing through the actual tool functions

## Critical Issues

### CR-01: Bottom-20% cleanup deletes already-deleted rows' worth of additional memory

**File:** `src/backend/services/memory_cleanup.py:63-82`
**Issue:** The Step 3 "bottom 20%" logic calculates `cutoff_count` and queries `access_count` values from the **current** state of the database — but Step 2 has already deleted all pre-quarter memories with `access_count <= 3`. This means the threshold is computed against a biased sample. More critically, the delete statement uses `WHERE access_count <= threshold` where `threshold` is the N-th value of the already-filtered set. This can delete far more than the intended 20% if many memories share the same `access_count` value as the threshold.

For example: if 100 pre-quarter memories remain after Step 2, all with `access_count` between 4 and 20, and 15 of them have `access_count=4`, the bottom 20% cutoff is 20 rows. The threshold becomes the 20th lowest `access_count` — say 5. The delete removes ALL rows with `access_count <= 5`, which could be 30+ rows (not the intended 20).

**Fix:**
```python
# Option A: Use a subquery to select exact IDs to delete, limiting to cutoff_count
from sqlalchemy import delete, func, select

sub = (
    select(AgentMemory.id)
    .where(AgentMemory.created_at < quarter_start)
    .order_by(AgentMemory.access_count.asc())
    .limit(cutoff_count)
)
result = await db_session.execute(
    delete(AgentMemory).where(AgentMemory.id.in_(sub))
)
removed_bottom_pct = result.rowcount
```

### CR-02: `build_skill_prompt` raises `FileNotFoundError` at runtime if prompt file is missing

**File:** `src/backend/services/skill_matcher.py:40`
**Issue:** `prompt_path.read_text(encoding="utf-8")` will raise `FileNotFoundError` if the prompt markdown file referenced in a skill JSON config doesn't exist. This is called from `build_agent_instructions()` which is in the hot path for every agent invocation. A misconfigured skill (e.g., typo in `prompt_file`) will crash the entire request with an unhandled exception.

**Fix:**
```python
def build_skill_prompt(matched_skills: list[SkillConfig]) -> str:
    if not matched_skills:
        return ""

    primary = matched_skills[0]
    prompt_path = SKILLS_DIR / "prompts" / primary.prompt_file

    try:
        primary_prompt = prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        import logging
        logging.getLogger(__name__).error(
            "Skill prompt file not found: %s (skill: %s)", prompt_path, primary.slug
        )
        primary_prompt = f"[技能：{primary.name}] {primary.description}"

    if len(matched_skills) == 1:
        return primary_prompt

    secondary_notes = []
    for skill in matched_skills[1:]:
        secondary_notes.append(
            f"{skill.name}方面：{skill.description}，请适当兼顾"
        )

    return f"{primary_prompt}\n\nAdditional guidance: {'。'.join(secondary_notes)}。"
```

## Warnings

### WR-01: `write_memory` upsert has a race condition under concurrent requests

**File:** `src/backend/tools/memory.py:50-78`
**Issue:** The upsert pattern (SELECT → check existence → UPDATE or INSERT) is not atomic. If two concurrent requests try to write the same `(user_id, key)`, both SELECTs return `None`, and both INSERT, creating a duplicate. SQLite's WAL mode allows concurrent reads but serializes writes, which mitigates this, but the pattern is still fragile if the session/transaction boundaries allow interleaving.

**Fix:** Add a unique constraint on `(user_id, key)` in the model and migration, and use `INSERT ... ON CONFLICT` (upsert) via SQLAlchemy's `insert().on_conflict_do_update()`. Alternatively, catch `IntegrityError` and retry the SELECT-UPDATE path.
```python
# In database.py, add to __table_args__:
Index("uq_agent_memories_user_key", "user_id", "key", unique=True),
```

### WR-02: `_score()` tie-breaking is undefined — memories with equal scores have arbitrary order

**File:** `src/backend/tools/memory.py:122-130`
**Issue:** When multiple memories have the same profile score (e.g., all score 0 when no `taste_tags` match or all have identical overlap), the sort order among tied memories is unstable. Per D-05, recency should be the fallback, but the code only uses recency when `taste_tags` is empty. When tags exist but no memory has overlapping tags, all scores are 0 and the order is arbitrary (Python's `sort` is stable, so it preserves insertion order, but that's not semantically meaningful).

**Fix:** Use a composite sort key that always includes recency as a tiebreaker:
```python
def _score(mem: AgentMemory) -> tuple[int, datetime]:
    tag_score = 0
    if taste_tags:
        try:
            val = json.loads(mem.value)
            mem_tags = val.get("tags", [])
            tag_score = len(set(taste_tags) & set(mem_tags))
        except (json.JSONDecodeError, TypeError, AttributeError):
            tag_score = 0
    return (tag_score, mem.updated_at)

memories = sorted(memories, key=_score, reverse=True)
```

### WR-03: `_load_all_skills` silently ignores malformed JSON files

**File:** `src/backend/services/skill_config.py:29-36`
**Issue:** If a JSON file in `data/skills/` is malformed or fails Pydantic validation, the entire `_load_all_skills()` function raises an exception — and because it's `@lru_cache`, the error is cached permanently. A single bad skill file breaks all skill loading for the lifetime of the process. This should either skip bad files with a warning or provide a clear error message.

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

@lru_cache
def _load_all_skills() -> dict[str, SkillConfig]:
    skills: dict[str, SkillConfig] = {}
    for path in SKILLS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            config = SkillConfig.model_validate(data)
            skills[config.slug] = config
        except Exception as e:
            logger.error("Failed to load skill config %s: %s", path, e)
    return skills
```

### WR-04: `rowcount` may be unreliable for async SQLite delete statements

**File:** `src/backend/services/memory_cleanup.py:44,52,82`
**Issue:** The cleanup code relies on `result.rowcount` to report how many rows were deleted. SQLAlchemy's `rowcount` behavior with async SQLite via aiosqlite can be unreliable — specifically, `rowcount` is set after `execute()` but before `flush()` in some dialect configurations. The code calls `flush()` at the end (line 84), but reads `rowcount` before that. This may work with aiosqlite but is a known edge case.

**Fix:** Move the `await db_session.flush()` to before reading stats, or use `RETURNING` / count queries instead of relying on `rowcount`.

### WR-05: `read_memories` does not update `last_accessed_at` or `access_count`

**File:** `src/backend/tools/memory.py:82-150`
**Issue:** Per D-11, "Writes increment access_count and update last_accessed_at and updated_at." The spec doesn't explicitly require reads to update these fields, but the cleanup logic (D-13) uses `access_count` to decide what to delete. If reads don't increment access_count, a frequently-read-but-never-rewritten memory could be cleaned up even though it's actively used. This creates a semantic mismatch between the access tracking and the cleanup algorithm.

**Fix:** Either (a) increment `access_count` and update `last_accessed_at` on read (at the cost of making reads write operations), or (b) document that `access_count` only tracks write/upsert frequency, not read frequency, and adjust cleanup logic accordingly.

## Info

### IN-01: Tests duplicate production logic instead of testing through tool functions

**File:** `tests/test_memory_skills_integration.py:56-141`
**Issue:** The test helpers `_write_memory()` and `_read_memories()` reimplement the production logic from `tools/memory.py` rather than calling the actual `@function_tool` functions via a mock `RunContextWrapper`. This means the tests verify the algorithm logic but don't test the tool interface, error handling, or the `ctx.context` DI wiring.

**Fix:** Construct a mock `RunContextWrapper[AgentContext]` and call `write_memory()` / `read_memories()` directly. This tests the actual tool code path:
```python
from agents import RunContextWrapper

def _make_ctx(session, user_id=None):
    context = AgentContext(
        db_session=session,
        amap_service=MagicMock(),
        user_id=user_id,
        settings=MagicMock(),
    )
    wrapper = MagicMock(spec=RunContextWrapper)
    wrapper.context = context
    return wrapper
```

### IN-02: `active_skills` field in `AgentContext` is never populated with matched skills

**File:** `src/backend/agent/context.py:28` and `src/backend/api/dependencies.py:124`
**Issue:** The `active_skills: list[str]` field was added to `AgentContext`, but `get_agent_context()` always initializes it as an empty list `[]`. The skill matching happens in `build_agent_instructions()` which is called separately. The field exists but is never populated, making it dead code. If Phase 14 needs to know which skills are active within a tool call, this wiring is missing.

**Fix:** Either populate `active_skills` in `get_agent_context()` if the user message is available, or document that it's reserved for Phase 14 pipeline integration.

### IN-03: Trip planning skill keywords too broad — "天" and "日" match casual messages

**File:** `data/skills/trip_planning.json:8`
**Issue:** The keywords `["天", "日"]` will match many casual Chinese messages that don't involve trip planning (e.g., "今天天气怎么样" → matches "天" and triggers trip_planning). Consider requiring `min_match: 2` for this skill or removing the single-character keywords.

**Fix:** Either increase `min_match` to 2, or replace `"天"` and `"日"` with compound keywords like `"几天"`, `"第一天"`, `"3天"` via substring matching refinement.

### IN-04: `test_memory_anonymous_rejected` test doesn't test the actual anonymous rejection path

**File:** `tests/test_memory_skills_integration.py:176-180`
**Issue:** The test queries for `AgentMemory` with `user_id == "nonexistent"` and asserts it returns `None`. This tests that no memories exist for a non-existent user, but it doesn't test the actual anonymous rejection logic (user_id=None returning empty list). The test name suggests it tests anonymous write rejection but it doesn't.

**Fix:** Test the actual `write_memory()` and `read_memories()` tool functions with `user_id=None` to verify anonymous users get "无法写入记忆" and "[]" respectively.

### IN-05: Missing Alembic migration unique index on `(user_id, key)`

**File:** `alembic/versions/a422b22ab4c1_add_agent_memories_table.py`
**Issue:** The migration creates a composite index on `(user_id, category)` but not a unique constraint on `(user_id, key)`. Per D-10, upsert is based on `(user_id, key)`, so without a unique constraint, duplicate keys are possible under race conditions (see WR-01). The index should be a unique index.

**Fix:** Add a unique index in the migration:
```python
op.create_index('uq_agent_memories_user_key', 'agent_memories', ['user_id', 'key'], unique=True)
```

---

_Reviewed: 2026-04-21T12:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
