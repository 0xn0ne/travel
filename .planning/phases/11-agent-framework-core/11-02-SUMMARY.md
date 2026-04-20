---
phase: 11-agent-framework-core
plan: 02
subsystem: agent
tags: [agent-loop, tool-calling, sse, fastapi-di, iteration-guard]

# Dependency graph
requires:
  - phase: 11-01
    provides: "LLMClient with tool_chat, ToolRegistry, ToolResult, EventBus"
provides:
  - "AgentLoop class with run() and run_streaming() methods"
  - "MAX_ITERATIONS = 8 guard with graceful forced final response"
  - "Tool error recovery — errors fed back as LLM context"
  - "SSE events: agent_thinking, tool_executing, tool_completed"
  - "get_agent_loop() and get_tool_registry() FastAPI dependencies"
affects: [12-agent-tools, 13-skills, 14-agent-stage, 15-chat-agent]

# Tech tracking
tech-stack:
  added: []
  patterns: [agent-tool-call-loop, iteration-guard, error-as-context, streaming-final-response]

key-files:
  created:
    - src/backend/agent/__init__.py
    - src/backend/agent/loop.py
  modified:
    - src/backend/api/dependencies.py

key-decisions:
  - "run() returns full text (non-streaming), run_streaming() yields chunks — same logic, different final output"
  - "EventBus not injected at DI level — provided at call sites in Phase 14/15"
  - "Placeholder tool executor in _execute_tool for Phase 12 real implementations"
  - "ToolExecutor type alias allows custom execution without modifying AgentLoop"

patterns-established:
  - "AgentLoop.run/run_streaming pattern: tool-call loop → max iteration guard → forced final response"
  - "stage='agent' SSE namespace coexists with pipeline stages (intent, prefilter, etc.)"
  - "Tool errors → ToolResult with error context → LLM decides recovery strategy"

requirements-completed: [AGENT-01, AGENT-04]

# Metrics
duration: 6min
completed: 2026-04-20
---

# Phase 11 Plan 02: AgentLoop Summary

**AgentLoop with tool-call cycle, 8-iteration guard, error recovery, SSE events, and FastAPI DI wiring**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-20T13:55:02Z
- **Completed:** 2026-04-20T14:01:02Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created AgentLoop class with run() (non-streaming) and run_streaming() (token-by-token) methods
- Implemented 8-iteration max guard with graceful forced final response in Chinese
- Tool errors caught and returned as error context to LLM for recovery (per D-15)
- SSE events emitted for agent_thinking, tool_executing, tool_completed via EventBus with stage="agent"
- Wired get_agent_loop() and get_tool_registry() into FastAPI dependency injection

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AgentLoop with tool-call cycle, iteration guard, and error recovery** - `4f3f721` (feat)
2. **Task 2: Wire AgentLoop into FastAPI dependencies** - `fab8393` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/backend/agent/__init__.py` - Package init re-exporting AgentLoop and MAX_ITERATIONS
- `src/backend/agent/loop.py` - AgentLoop class with run(), run_streaming(), _execute_tool(), _emit()
- `src/backend/api/dependencies.py` - Added get_tool_registry() and get_agent_loop() dependencies

## Decisions Made
- EventBus not injected at FastAPI DI level — will be provided at call sites (PipelineCoordinator in Phase 14, Chat endpoint in Phase 15) for clean separation
- ToolExecutor type alias (Callable[[str, str], Awaitable[ToolResult]]) allows custom tool execution in Phase 12 without modifying AgentLoop
- Placeholder tool executor returns ToolResult with error message indicating Phase 12 implementation needed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All key files verified on disk. Both task commits confirmed in git log. Plan-level verification commands pass:
1. ✅ from backend.agent import AgentLoop
2. ✅ MAX_ITERATIONS == 8
3. ✅ from backend.api.dependencies import get_agent_loop, get_tool_registry
4. ✅ Cross-module integration (ToolRegistry + AgentLoop)
5. ✅ SSE stage="agent" in loop.py

## Next Phase Readiness
- AgentLoop ready for Phase 12 (real tool implementations via ToolExecutor)
- FastAPI DI ready for Phase 14 (Agent Stage) and Phase 15 (Chat endpoint)
- EventBus SSE events ready for frontend integration

---
*Phase: 11-agent-framework-core*
*Completed: 2026-04-20*
