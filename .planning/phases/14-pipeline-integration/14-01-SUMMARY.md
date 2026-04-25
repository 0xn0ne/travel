---
phase: 14
plan: 01
status: complete
self_check: PASSED
key_files:
  created:
    - src/backend/pipeline/stages/stage_agent.py
    - tests/test_stage_agent.py
  modified:
    - src/backend/pipeline/stages/__init__.py
---

# Plan 14-01: Agent Enrichment Stage

## What Was Built

Agent enrichment stage that inserts between POI filtering and itinerary generation in the pipeline.

### Core Components

1. **`agent_enrich()`** (`stage_agent.py:89-150`)
   - Async function receiving llm_client, intent, poi_candidates, user_input, event_bus, agent_context
   - Uses SDK `Runner.run()` with cached Agent from `get_sdk_agent()`, overriding instructions via `build_agent_instructions()`
   - 30-second timeout with graceful degradation (returns `""` on failure)
   - Extracts final text output from `RunResult.final_output`
   - Emits `agent_error` event on failure

2. **`PipelineSSEHooks`** (`stage_agent.py:23-82`)
   - Extends `RunHooksBase` for SSE event emission during agent tool calls
   - `on_tool_start`: emits `tool_executing` event with Chinese display name from `_TOOL_DISPLAY_NAMES`
   - `on_tool_end`: emits `tool_completed` event with completion message
   - Constructor takes EventBus and optional event bus queue

3. **`_TOOL_DISPLAY_NAMES`** (`stage_agent.py:14-21`)
   - Maps 12 tool function names to `(executing_msg, completed_msg)` Chinese tuples
   - Tools: search_pois, query_weather, get_user_preferences, get_itinerary_context, web_search, web_fetch, list_files, read_file, write_file, execute_command, read_memories, write_memory

### Agent Instructions

System prompt includes city, intent summary (interests + pace + budget), POI count, and instruction to enrich (not replace) POI data. Agent instructed to use search tools for supplementary information.

### Tests

7 unit tests in `tests/test_stage_agent.py`:
- `test_agent_enrich_returns_text`: Happy path with mocked Runner
- `test_agent_enrich_timeout`: asyncio.TimeoutError → returns ""
- `test_agent_enrich_runner_error`: Generic exception → returns ""
- `test_agent_enrich_no_context`: None agent_context → returns ""
- `test_sse_hooks_tool_start`: on_tool_start emits correct event
- `test_sse_hooks_tool_end`: on_tool_end emits correct event
- `test_sse_hooks_unknown_tool`: Unknown tool falls back to generic message

## Commits

- `aecc1c7`: feat(14-01): add agent enrichment stage with SSE hooks

## Deviations

None. Implementation follows plan exactly.
