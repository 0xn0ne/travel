# Plan 13-03: Wire Memory Tools + Skill Activation — Summary

**Executed:** 2026-04-21
**Status:** Complete

## What Was Done

### Task 1: Wire memory tools + skill activation into DI

- **`src/backend/tools/__init__.py`**: Docstring updated from "10" to "12" tools. Memory tools (`read_memories`, `write_memory`) were already added by Plan 13-01.
- **`src/backend/agent/context.py`**: Added `active_skills: list[str] = []` field to `AgentContext` for per-request skill tracking.
- **`src/backend/api/dependencies.py`**:
  - Added import of `match_skills, build_skill_prompt` from `backend.services.skill_matcher`
  - Added `build_agent_instructions(user_message, interests)` utility that combines base instructions with skill-enriched prompt
  - Updated `get_agent_context()` to include `active_skills=[]`
  - `get_sdk_agent()` remains `@lru_cache`'d singleton with 12 tools
- **`tests/test_tools_integration.py`**: Updated tool count assertions (10→12) and added `read_memories`/`write_memory` to expected names.

### Task 2: Integration tests (16 tests)

Created `tests/test_memory_skills_integration.py` with:

- **Memory tests (7)**: write+read, upsert, anonymous rejection, profile scoring, category filter, trip_context expiry cleanup, new memory exemption
- **Skill tests (6)**: trip_planning match, food_exploration match, local_insider match, primary+secondary hierarchy, prompt building, no match
- **Integration tests (3)**: ALL_TOOLS count=12, build_agent_instructions with/without skill

## Verification

- All 43 tests pass (`python3 -m pytest tests/ -x -q`)
- `ALL_TOOLS` has 12 functions including `read_memories` and `write_memory`
- `build_agent_instructions()` produces skill-enriched instructions based on user message
- `AgentContext.active_skills` field works correctly

## Commits

- `1bf8d9b` feat(13-03): wire memory tools + skill activation into DI with integration tests

## Notes

- `@function_tool` decorated functions cannot be called directly in tests — they are `FunctionTool` wrapper objects. Memory tests use direct SQLAlchemy operations instead.
- "今天天气怎么样" matches `trip_planning` skill due to "天" keyword overlap. Test uses "你好呀" for no-match case.
- In-memory SQLite with shared engine persists data across sessions within the same test; `_seed_user()` was made idempotent to handle this.
