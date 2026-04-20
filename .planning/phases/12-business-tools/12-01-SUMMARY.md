---
phase: 12-business-tools
plan: 01
subsystem: agent
tags: [openai-agents, sdk, deepseek, pydantic, chatcompletions]

# Dependency graph
requires:
  - phase: 11-agent-foundation
    provides: AgentLoop, ToolRegistry, ToolResult — existing agent infrastructure
provides:
  - AgentContext Pydantic model for SDK tool DI
  - create_deepseek_model() helper for SDK model configuration
  - init_agent_sdk() startup function for ChatCompletions API
  - SDK foundation for Phase 12 tool implementations
affects: [12-02, 12-03, 12-04, 14-pipeline-integration, 15-chat]

# Tech tracking
tech-stack:
  added: [openai-agents>=0.14.2, ddgs]
  patterns: [SDK Agent with OpenAIChatCompletionsModel, AgentContext DI via RunContextWrapper, set_default_openai_api chat_completions startup]

key-files:
  created: [src/backend/agent/context.py, tests/test_agent_context.py]
  modified: [pyproject.toml, src/backend/agent/__init__.py, src/backend/tools/__init__.py, src/backend/main.py]

key-decisions:
  - "AgentContext uses Any for db_session and settings (Pydantic can't serialize AsyncSession/Settings)"
  - "amap_service retains AmapService type for DI type safety — tests use real AmapService with test key"
  - "init_agent_sdk() called after init_db() in lifespan — SDK needs no DB but follows init order"

patterns-established:
  - "SDK startup pattern: set_default_openai_api('chat_completions') once at app init for DeepSeek"
  - "Context DI pattern: AgentContext holds request-scoped services, injected via RunContextWrapper into @function_tool"
  - "Model factory pattern: create_deepseek_model() wraps AsyncOpenAI + OpenAIChatCompletionsModel"

requirements-completed: [AGENT-01, AGENT-02]

# Metrics
duration: 5min
completed: 2026-04-20
---

# Phase 12 Plan 01: SDK Foundation Summary

**OpenAI Agents SDK foundation: AgentContext Pydantic model, create_deepseek_model() helper, init_agent_sdk() startup hook, and 5 passing integration tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-20T15:49:58Z
- **Completed:** 2026-04-20T15:55:06Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Installed openai-agents SDK and ddgs dependencies
- Created AgentContext Pydantic model with db_session, amap_service, user_id, settings fields
- Created create_deepseek_model() factory for DeepSeek ChatCompletions
- Wired init_agent_sdk() into FastAPI lifespan for startup configuration
- Verified SDK Agent construction with DeepSeek model via 5 integration tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Install SDK dependencies and create AgentContext model** - `a4356ab` (feat)
2. **Task 2: Wire init_agent_sdk into startup + verify with integration test** - `8f255a9` (feat)

## Files Created/Modified
- `pyproject.toml` - Added openai-agents>=0.14.2 and ddgs dependencies
- `src/backend/agent/context.py` - AgentContext Pydantic model + create_deepseek_model() factory
- `src/backend/agent/__init__.py` - init_agent_sdk() function + AgentContext/create_deepseek_model exports
- `src/backend/tools/__init__.py` - Updated docstring with Phase 12 migration notes
- `src/backend/main.py` - Added init_agent_sdk() call in lifespan
- `tests/test_agent_context.py` - 5 integration tests for SDK foundation

## Decisions Made
- AgentContext uses `Any` for db_session and settings fields — Pydantic cannot serialize AsyncSession or Settings objects
- amap_service retains `AmapService` type annotation for type-safe DI — tests use real AmapService with test API key rather than MagicMock
- init_agent_sdk() called after init_db() in lifespan order — SDK itself doesn't need DB but follows established startup sequence

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test mocking for AmapService type validation**
- **Found during:** Task 2 (TDD RED phase)
- **Issue:** MagicMock fails Pydantic's is_instance_of validation for `amap_service: AmapService` field
- **Fix:** Tests create real `AmapService(api_key="test-key")` instances instead of MagicMock
- **Files modified:** tests/test_agent_context.py
- **Verification:** All 5 tests pass
- **Committed in:** 8f255a9 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test adjustment necessary for correctness with Pydantic type validation. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SDK foundation complete — openai-agents importable, AgentContext model ready
- Ready for Plan 02 (TOOL-01 Web Search + TOOL-02 POI Search) and Plan 03 (TOOL-03 Weather + TOOL-04 Route)
- AgentLoop legacy retained for backward compatibility during migration (retires in Plan 04)

## Self-Check: PASSED

- All 6 files exist on disk
- Both commits (a4356ab, 8f255a9) found in git log
- All 5 integration tests pass
- All acceptance criteria verified

---
*Phase: 12-business-tools*
*Completed: 2026-04-20*
