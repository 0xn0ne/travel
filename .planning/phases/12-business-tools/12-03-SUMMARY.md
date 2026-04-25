---
phase: 12-business-tools
plan: 03
subsystem: tools
tags: [ddgs, httpx, ssrf, sandbox, file-io, function-tool]

# Dependency graph
requires:
  - phase: 12-01
    provides: AgentContext model and SDK setup
provides:
  - web_search tool (DuckDuckGo, cn-zh region)
  - web_fetch tool (httpx + SSRF protection)
  - file_io tools (sandboxed read/write/list in data/agent_memory/)
  - command_exec stub (disabled)
affects: [12-04, 12-05, agent-integration]

# Tech tracking
tech-stack:
  added: [ddgs]
  patterns: [WebSearchProvider protocol, SSRF IP validation, path traversal protection via resolve()+is_relative_to()]

key-files:
  created:
    - src/backend/tools/web_search.py
    - src/backend/tools/web_fetch.py
    - src/backend/tools/file_io.py
    - src/backend/tools/command_exec.py
  modified: []

key-decisions:
  - "DuckDuckGo search wrapped in WebSearchProvider protocol for future provider swap"
  - "SSRF protection via DNS resolution + ipaddress private IP check before fetching"
  - "File I/O sandboxed per-user under data/agent_memory/{user_id}/ with Path.resolve() + is_relative_to()"
  - "Command exec is a stub returning disabled message — reserved for future enablement"

patterns-established:
  - "WebSearchProvider protocol: async search(query, max_results) → list[dict] for provider abstraction"
  - "SSRF validation: _validate_url() resolves hostname, checks all returned IPs against private ranges"
  - "Path sandbox: _validate_path() resolves to absolute, checks is_relative_to(SANDBOX_ROOT)"

requirements-completed: [TOOL-01, TOOL-02, TOOL-03, TOOL-04]

# Metrics
duration: 3min
completed: 2026-04-20
---

# Phase 12 Plan 03: General-Purpose Tools Summary

**DuckDuckGo web search, httpx web fetch with SSRF protection, sandboxed file I/O, and command exec stub — all using @function_tool with AgentContext DI**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-20T16:08:03Z
- **Completed:** 2026-04-20T16:11:20Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Web search tool with DuckDuckGo (cn-zh region, top 5 results) and WebSearchProvider protocol for future swap
- Web fetch tool with SSRF protection (DNS resolution → private IP blocking), HTML stripping, 3000-char truncation
- Sandboxed file I/O (list/read/write) under data/agent_memory/{user_id}/ with path traversal protection
- Command exec stub returning disabled message — tool interface defined for future enablement

## Task Commits

Each task was committed atomically:

1. **Task 1: Web search and web fetch tools** - `7fb3dee` (feat)
2. **Task 2: File I/O and command exec tools** - `3fedb9f` (feat)

## Files Created/Modified
- `src/backend/tools/web_search.py` - DuckDuckGo search tool with WebSearchProvider protocol
- `src/backend/tools/web_fetch.py` - URL fetch tool with SSRF protection and content extraction
- `src/backend/tools/file_io.py` - Sandboxed file I/O (list_files, read_file, write_file)
- `src/backend/tools/command_exec.py` - Command execution stub (disabled)

## Decisions Made
- DuckDuckGo search uses asyncio.to_thread() since DDGS is synchronous
- WebSearchProvider protocol defined as typing.Protocol for clean provider swap later
- SSRF validation blocks all private/reserved IPs including IPv6 loopback and link-local
- File sandbox creates per-user directories on first write, not at startup
- Simple regex-based HTML stripping for MVP (no BeautifulSoup dependency)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 4 general-purpose tools (TOOL-01 through TOOL-04) implemented and importable
- Tools follow established @function_tool + AgentContext DI pattern from Wave 1
- Ready for Wave 3 (Plan 04: agent integration) or continuation of remaining plans

---
*Phase: 12-business-tools*
*Completed: 2026-04-20*
