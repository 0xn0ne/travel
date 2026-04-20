---
phase: 11-agent-framework-core
plan: 01
subsystem: agent
tags: [openai, tool-calling, function-calling, yaml, llm-client]

# Dependency graph
requires:
  - phase: prior-phases
    provides: "DeepSeekClient, existing pipeline, FastAPI DI"
provides:
  - "LLMClient with stream_chat, generate_json, tool_chat"
  - "ToolRegistry loading tool schemas from config.yml"
  - "ToolResult unified output format"
  - "config.yml with search_pois example tool definition"
affects: [12-agent-tools, 13-skills, 14-agent-stage, 15-chat-agent]

# Tech tracking
tech-stack:
  added: [pyyaml>=6.0]
  patterns: [openai-function-calling, yaml-tool-config, tool-result-dataclass]

key-files:
  created:
    - src/backend/tools/__init__.py
    - src/backend/tools/result.py
    - src/backend/tools/registry.py
    - config.yml
  modified:
    - src/backend/llm/client.py
    - src/backend/llm/__init__.py
    - src/backend/api/dependencies.py
    - src/backend/pipeline/coordinator.py
    - src/backend/pipeline/stages/stage1_intent.py
    - src/backend/pipeline/stages/stage3_generate.py
    - src/backend/api/routes/generate.py
    - src/backend/api/routes/adjust.py
    - src/backend/api/routes/test_runner.py
    - src/backend/services/test_runner.py
    - pyproject.toml

key-decisions:
  - "LLMClient renamed from DeepSeekClient with backward-compatible alias"
  - "Tool definitions centralized in config.yml (YAML) for startup loading"
  - "ToolResult dataclass with data/error/summary fields for unified tool output"
  - "tool_chat() uses non-streaming mode for stable function calling"

patterns-established:
  - "Tool schema in config.yml → ToolRegistry → OpenAI function-calling format"
  - "ToolResult as universal return type for all tool invocations"
  - "LLMClient as single entry point for all LLM interaction modes"

requirements-completed: [AGENT-02]

# Metrics
duration: 10min
completed: 2026-04-20
---

# Phase 11 Plan 01: Agent Foundation Summary

**LLMClient with tool_chat, ToolRegistry from config.yml, and ToolResult unified output format**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-20T13:37:40Z
- **Completed:** 2026-04-20T13:48:18Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- Replaced DeepSeekClient with LLMClient supporting 3 modes: stream_chat, generate_json, tool_chat
- Created ToolRegistry that loads tool schemas from config.yml and produces OpenAI function-calling format
- Defined ToolResult dataclass as unified tool output format with data/error/summary fields
- Added search_pois example tool definition in config.yml to demonstrate the schema

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ToolResult + ToolRegistry + config.yml** - `3b7cf7b` (feat)
2. **Task 2: Replace DeepSeekClient with LLMClient** - `3cd3b1c` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/backend/tools/__init__.py` - Package init re-exporting ToolResult and ToolRegistry
- `src/backend/tools/result.py` - ToolResult dataclass with data/error/summary and to_dict()
- `src/backend/tools/registry.py` - ToolRegistry class loading from config.yml, OpenAI format output
- `config.yml` - Centralized tool schema definitions with search_pois example
- `src/backend/llm/client.py` - LLMClient class (renamed from DeepSeekClient) with tool_chat()
- `src/backend/llm/__init__.py` - Updated exports for LLMClient, DeepSeekClient alias
- `src/backend/api/dependencies.py` - get_llm_client() returns LLMClient
- `src/backend/pipeline/coordinator.py` - TYPE_CHECKING import updated to LLMClient
- `src/backend/pipeline/stages/stage1_intent.py` - Type hints updated to LLMClient
- `src/backend/pipeline/stages/stage3_generate.py` - Type hints updated to LLMClient
- `src/backend/api/routes/generate.py` - Import and type hint updated to LLMClient
- `src/backend/api/routes/adjust.py` - Import and type hint updated to LLMClient
- `src/backend/api/routes/test_runner.py` - Import and type hint updated to LLMClient
- `src/backend/services/test_runner.py` - Import and type hint updated to LLMClient
- `pyproject.toml` - Added pyyaml>=6.0 dependency

## Decisions Made
- Kept DeepSeekClient as backward-compatible alias (`DeepSeekClient = LLMClient`) to avoid breaking any external consumers
- Tool definitions use YAML (not JSON) for better readability and comment support in config.yml
- Tool registration is static at startup — no dynamic registration methods (reserved for Skills in Phase 13)
- tool_chat uses non-streaming mode for stable DeepSeek function calling (per D-07)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All key files verified on disk. Both task commits confirmed in git log. Plan-level verification commands pass.

## Next Phase Readiness
- Agent foundation ready: LLMClient with tool_chat, ToolRegistry, ToolResult all functional
- Ready for Plan 02 (AgentLoop) which depends on these components
- config.yml demonstrates schema format; Phase 12 will add real tool implementations

---
*Phase: 11-agent-framework-core*
*Completed: 2026-04-20*
