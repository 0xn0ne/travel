---
phase: 12-business-tools
plan: 02
subsystem: agent-tools
tags: [amap, weather, poi-search, user-preferences, itinerary-context, openai-agents-sdk, function-tool]

# Dependency graph
requires:
  - phase: 12-business-tools/01
    provides: AgentContext model, OpenAI Agents SDK integration, @function_tool decorator pattern
provides:
  - POI search tool (BIZ-01): DB-first + Amap fallback search
  - Weather query tool (BIZ-02): 高德 weather API with adcode resolution
  - User preferences tool (BIZ-03): taste tags, budget, recent itineraries
  - Itinerary context tool (BIZ-04): day-by-day parsed itinerary data
  - AmapService.get_weather() method with live conditions + forecast
  - CityConfig.adcode field for weather API city resolution
affects: [12-business-tools/03, 12-business-tools/04, agent-tool-registration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@function_tool with RunContextWrapper[AgentContext] DI for all business tools"
    - "DB-first query with Amap API fallback for POI search"
    - "CityConfig adcode mapping for weather API city resolution"

key-files:
  created:
    - src/backend/tools/search_pois.py
    - src/backend/tools/weather.py
    - src/backend/tools/user_prefs.py
    - src/backend/tools/itinerary_context.py
  modified:
    - src/backend/services/amap_service.py
    - src/backend/services/city_config.py
    - data/cities/hangzhou.json
    - data/cities/shanghai.json

key-decisions:
  - "Used CityConfig.adcode field for weather API instead of 高德 district API (per D-28)"
  - "DB-first POI search with Python-level taste_tags matching (SQLite contains unreliable for JSON)"
  - "Amap API fallback only triggers when DB results < 3 (per D-25)"
  - "Travel weather suggestions based on weather condition keywords"

patterns-established:
  - "Business tool pattern: @function_tool + RunContextWrapper[AgentContext] + formatted Chinese text output"
  - "Graceful degradation: tools return Chinese error messages, never crash on missing data"

requirements-completed: [BIZ-01, BIZ-02, BIZ-03, BIZ-04]

# Metrics
duration: 6min
completed: 2026-04-20
---

# Phase 12 Plan 02: Business Tools Summary

**4 business tools (POI search, weather, user prefs, itinerary context) with AmapService weather extension, all using @function_tool DI pattern**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-20T15:59:06Z
- **Completed:** 2026-04-20T16:05:36Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `get_weather()` to AmapService with live conditions + forecast, using adcode resolution via CityConfig
- Created 4 @function_tool decorated business tools with AgentContext DI
- Extended CityConfig model and city JSON files with `adcode` field for weather API
- All tools return formatted Chinese text with graceful error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Add get_weather() to AmapService + implement POI search and weather tools** - `e547b72` (feat)
2. **Task 2: Implement user preferences and itinerary context tools** - `b668cb8` (feat)

## Files Created/Modified
- `src/backend/tools/search_pois.py` - POI search tool: DB-first query + Amap API fallback, top 10 results with tier/rating/highlight
- `src/backend/tools/weather.py` - Weather query tool: formatted forecast with travel suggestions
- `src/backend/tools/user_prefs.py` - User preferences tool: taste_tags, budget, last 3 itineraries
- `src/backend/tools/itinerary_context.py` - Itinerary context tool: day-by-day POI breakdown from parsed JSON
- `src/backend/services/amap_service.py` - Added get_weather() method with live + forecast weather queries
- `src/backend/services/city_config.py` - Added adcode field to CityConfig model
- `data/cities/hangzhou.json` - Added adcode "330100" for weather API
- `data/cities/shanghai.json` - Added adcode "310000" for weather API

## Decisions Made
- Used CityConfig.adcode for weather resolution (avoids extra API call to 高德 district API)
- DB-first POI search with Python-level JSON parsing for taste_tags (SQLite contains unreliable for JSON arrays)
- Amap API fallback only when DB results < 3 (balances curated data with coverage)
- Weather tool includes travel suggestions based on weather keywords (rain → bring umbrella, sunny → outdoor activities)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 4 business tools (BIZ-01 through BIZ-04) implemented and verified
- Ready for Plan 03 (general tools: web search, web fetch, file I/O, command exec stub)
- Ready for Plan 04 (tool registration with Agent, DI wiring)

## Self-Check: PASSED

All 8 files verified on disk. Both task commits (e547b72, b668cb8) found in git log. All acceptance criteria passed.

---
*Phase: 12-business-tools*
*Completed: 2026-04-20*
