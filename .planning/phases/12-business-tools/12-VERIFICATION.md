---
phase: 12-business-tools
verified: 2026-04-21T01:00:00Z
status: human_needed
score: 16/16 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Call search_pois tool with a real DB session + Amap API key and verify it returns POI results with name, rating, tier, coords"
    expected: "Formatted Chinese text listing POIs with tier badges, ratings, coordinates"
    why_human: "Requires running server with DB seeded and valid Amap API key — cannot verify DB query + Amap fallback end-to-end programmatically"
  - test: "Call query_weather tool with city='上海' and verify formatted forecast with travel suggestions"
    expected: "Weather data with current conditions + multi-day forecast + travel suggestions per day"
    why_human: "Requires valid Amap API key to call 高德 weather API — external service dependency"
  - test: "Call web_search tool with a query and verify DuckDuckGo returns results"
    expected: "Top 5 results with title, snippet, URL in Chinese text format"
    why_human: "External DuckDuckGo API dependency — network call to third-party service"
---

# Phase 12: Business & General Tools Verification Report

**Phase Goal:** Agent has a complete toolkit to help travelers — search POIs, check weather, read preferences, search the web, and manage files
**Verified:** 2026-04-21T01:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | openai-agents SDK is importable and functional | ✓ VERIFIED | pyproject.toml has `openai-agents>=0.14.2`; `from agents import Agent, function_tool, RunContextWrapper` succeeds; tests pass |
| 2 | AgentContext Pydantic model holds all request-scoped services | ✓ VERIFIED | `src/backend/agent/context.py`: class AgentContext with db_session, amap_service, user_id, settings fields; Pydantic BaseModel with ConfigDict(arbitrary_types_allowed=True) |
| 3 | A basic Agent can be constructed with SDK tools and DeepSeek model | ✓ VERIFIED | `create_deepseek_model()` returns `OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=AsyncOpenAI(...))`; `test_sdk_agent_construction` passes |
| 4 | set_default_openai_api('chat_completions') is called at startup | ✓ VERIFIED | `init_agent_sdk()` in `agent/__init__.py` calls `set_default_openai_api("chat_completions")`; wired into `main.py` lifespan at line 88 |
| 5 | Agent can search POIs by city+keyword and get name, rating, tier, coords, highlight_note | ✓ VERIFIED | `search_pois.py` (122 LOC): @function_tool, queries DB via SQLAlchemy `select(POI)`, falls back to `amap_service.search_pois()`, taste_tags JSON post-filter, top 10 with truncation note |
| 6 | Agent can query weather for a city and date range with temperature and conditions | ✓ VERIFIED | `weather.py` (84 LOC): @function_tool, calls `amap_service.get_weather()`, formats forecast with travel suggestions; `amap_service.py` has `get_weather()` (82 LOC) with live+forecast via 高德 API + adcode resolution |
| 7 | Agent can read user taste_tags, budget, and last 3 itineraries | ✓ VERIFIED | `user_prefs.py` (75 LOC): @function_tool, queries User model, `json.loads(taste_tags_default)`, reads last 3 ItineraryRow entries; handles unauthenticated gracefully |
| 8 | Agent can read current itinerary POIs and day structure | ✓ VERIFIED | `itinerary_context.py` (76 LOC): @function_tool, queries ItineraryRow by id, `json.loads(parsed_itinerary)`, formats day-by-day breakdown |
| 9 | Agent can search the web by keywords and get top 5 results with title+snippet+URL | ✓ VERIFIED | `web_search.py` (101 LOC): @function_tool, DuckDuckGoSearchProvider with `DDGS().text(query, region="cn-zh", max_results=5)`, WebSearchProvider protocol, asyncio.to_thread for sync DDGS |
| 10 | Agent can fetch a URL and get text content (max 3000 chars) | ✓ VERIFIED | `web_fetch.py` (236 LOC): @function_tool, SSRF protection with `_is_private_ip()` + DNS resolution + IP pinning + redirect validation, HTML stripping, 3000-char truncation, source URL included |
| 11 | Agent can read/write files within data/agent_memory/ but not outside | ✓ VERIFIED | `file_io.py` (159 LOC): 3 @function_tool functions (list_files, read_file, write_file), SANDBOX_ROOT = `data/agent_memory/`, `_validate_path()` with `Path.resolve()` + `is_relative_to()`, per-user subdirectories, auth check |
| 12 | Command exec stub exists and returns disabled message | ✓ VERIFIED | `command_exec.py` (25 LOC): @function_tool, returns "⚠️ 命令执行功能暂未开放，敬请期待后续版本。" |
| 13 | FastAPI DI constructs AgentContext per-request with all services | ✓ VERIFIED | `dependencies.py`: `get_agent_context()` uses `Depends(get_db)`, `Depends(get_amap_service)`, `Depends(get_current_user_optional)`, constructs AgentContext |
| 14 | SDK Agent can be built with all 8 tools registered | ✓ VERIFIED | `dependencies.py`: `get_sdk_agent()` returns `Agent(name="拾途助手", tools=ALL_TOOLS, model=model)`; ALL_TOOLS has 10 functions (file_io has 3) |
| 15 | Tool module exports are centralized in tools/__init__.py | ✓ VERIFIED | `tools/__init__.py`: ALL_TOOLS list with all 10 tool functions imported from their modules |
| 16 | Integration test verifies SDK Agent + tools construction | ✓ VERIFIED | `test_tools_integration.py`: 5 tests verifying tool count (10), agent construction, tool names, identifier validity, context creation — all pass |

**Score:** 16/16 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Dependencies: openai-agents, ddgs | ✓ VERIFIED | Contains `openai-agents>=0.14.2` and `ddgs` |
| `src/backend/agent/context.py` | AgentContext Pydantic model | ✓ VERIFIED | 51 LOC, class AgentContext with 4 fields + create_deepseek_model factory |
| `src/backend/agent/__init__.py` | SDK startup init + exports | ✓ VERIFIED | 31 LOC, init_agent_sdk(), exports AgentContext, create_deepseek_model |
| `src/backend/tools/search_pois.py` | POI search tool (BIZ-01) | ✓ VERIFIED | 122 LOC, DB-first + Amap fallback, taste_tags matching, top 10 |
| `src/backend/tools/weather.py` | Weather query tool (BIZ-02) | ✓ VERIFIED | 84 LOC, formatted forecast with travel suggestions |
| `src/backend/tools/user_prefs.py` | User preferences tool (BIZ-03) | ✓ VERIFIED | 75 LOC, taste_tags, budget, last 3 itineraries |
| `src/backend/tools/itinerary_context.py` | Itinerary context tool (BIZ-04) | ✓ VERIFIED | 76 LOC, day-by-day parsed itinerary breakdown |
| `src/backend/tools/web_search.py` | Web search tool (TOOL-01) | ✓ VERIFIED | 101 LOC, DDGS with cn-zh region, WebSearchProvider protocol |
| `src/backend/tools/web_fetch.py` | Web fetch tool (TOOL-02) | ✓ VERIFIED | 236 LOC, SSRF protection with DNS resolution + IP pinning |
| `src/backend/tools/file_io.py` | File I/O tool (TOOL-03) | ✓ VERIFIED | 159 LOC, 3 @function_tool functions with sandbox |
| `src/backend/tools/command_exec.py` | Command exec stub (TOOL-04) | ✓ VERIFIED | 25 LOC, disabled message stub |
| `src/backend/services/amap_service.py` | Weather API method | ✓ VERIFIED | get_weather() added (82 LOC), live+forecast queries |
| `src/backend/services/city_config.py` | adcode field | ✓ VERIFIED | `adcode: str` field added to CityConfig |
| `data/cities/hangzhou.json` | adcode field | ✓ VERIFIED | `"adcode": "330100"` |
| `data/cities/shanghai.json` | adcode field | ✓ VERIFIED | `"adcode": "310000"` |
| `src/backend/api/dependencies.py` | DI with AgentContext + SDK agent | ✓ VERIFIED | get_agent_context(), get_sdk_agent() with lru_cache |
| `src/backend/tools/__init__.py` | Centralized tool exports | ✓ VERIFIED | ALL_TOOLS list with 10 function imports |
| `tests/test_agent_context.py` | SDK foundation tests | ✓ VERIFIED | 5 tests, all pass |
| `tests/test_tools_integration.py` | Integration tests | ✓ VERIFIED | 5 tests, all pass |
| `src/backend/main.py` | init_agent_sdk wired in lifespan | ✓ VERIFIED | Line 88: `init_agent_sdk()` called in lifespan after init_db() |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tools/search_pois.py` | `amap_service.py` | `ctx.context.amap_service.search_pois()` | ✓ WIRED | Line 82: `amap_service.search_pois(keywords=..., city=...)` |
| `tools/weather.py` | `amap_service.py` | `ctx.context.amap_service.get_weather()` | ✓ WIRED | Line 43: `await amap_service.get_weather(city_name=city, days=days)` |
| `tools/user_prefs.py` | `database.py` | User model query via `ctx.context.db_session` | ✓ WIRED | Lines 31-32: `select(User).where(User.id == user_id)`, lines 46-51: ItineraryRow query |
| `tools/itinerary_context.py` | `database.py` | ItineraryRow query via `ctx.context.db_session` | ✓ WIRED | Lines 31-33: `select(ItineraryRow).where(ItineraryRow.id == itinerary_id)` |
| `tools/web_search.py` | ddgs package | `DDGS().text()` call | ✓ WIRED | Line 63: `ddgs.text(query, region="cn-zh", max_results=max_results)` via asyncio.to_thread |
| `tools/web_fetch.py` | httpx | `httpx.AsyncClient` for URL fetching | ✓ WIRED | Lines 164-168: `httpx.AsyncClient(timeout=15.0, follow_redirects=False, verify=ssl_context)` |
| `tools/file_io.py` | `data/agent_memory/` | Path operations within sandbox | ✓ WIRED | Line 21: `SANDBOX_ROOT = Path("data/agent_memory").resolve()`, line 42: `_validate_path()` with `is_relative_to()` |
| `dependencies.py` | `agent/context.py` | AgentContext construction with DI services | ✓ WIRED | Lines 111-123: `get_agent_context()` with Depends for db, amap, user |
| `dependencies.py` | `tools/*.py` | Tool imports for SDK Agent | ✓ WIRED | Line 16: `from backend.tools import ALL_TOOLS`, line 137: `tools=ALL_TOOLS` |
| `agent/__init__.py` | agents SDK | `set_default_openai_api` import | ✓ WIRED | Line 10: `from agents import set_default_openai_api`, line 22: `set_default_openai_api("chat_completions")` |
| `main.py` | `agent/__init__.py` | `init_agent_sdk()` call in lifespan | ✓ WIRED | Line 24: `from backend.agent import init_agent_sdk`, line 88: `init_agent_sdk()` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `search_pois.py` | db_pois, amap results | DB `select(POI)` + `amap_service.search_pois()` | ✓ DB query + Amap API | ✓ FLOWING |
| `weather.py` | weather data | `amap_service.get_weather()` → 高德 API | ✓ Live + forecast API calls | ✓ FLOWING |
| `user_prefs.py` | user, itineraries | DB `select(User)` + `select(ItineraryRow)` | ✓ DB queries with real models | ✓ FLOWING |
| `itinerary_context.py` | parsed itinerary | DB `select(ItineraryRow)` + `json.loads(parsed_itinerary)` | ✓ DB query + JSON parse | ✓ FLOWING |
| `web_search.py` | search results | `DDGS().text()` → DuckDuckGo | ✓ External API call | ✓ FLOWING |
| `web_fetch.py` | page content | `httpx.AsyncClient.get()` → URL fetch + HTML strip | ✓ HTTP fetch + text extraction | ✓ FLOWING |
| `file_io.py` | file content | `path.read_text()` / `path.write_text()` | ✓ Real filesystem I/O | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ALL_TOOLS has 10 entries | `python3 -c "from backend.tools import ALL_TOOLS; assert len(ALL_TOOLS) == 10"` | 10 tools, all names correct | ✓ PASS |
| SDK Agent constructable with all tools | `pytest tests/test_tools_integration.py -v` | 5/5 tests pass in 1.84s | ✓ PASS |
| SDK foundation tests pass | `pytest tests/test_agent_context.py -v` | 5/5 tests pass | ✓ PASS |
| create_deepseek_model returns correct model | `python3 -c "from backend.agent.context import create_deepseek_model; m=create_deepseek_model('k'); assert m.model=='deepseek-chat'"` | model attribute = "deepseek-chat" | ✓ PASS |
| All tool imports succeed | `python3 -c "from backend.tools import ALL_TOOLS; from backend.api.dependencies import get_agent_context, get_sdk_agent"` | All imports OK | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BIZ-01 | 12-02 | POI search tool — agent searches POI DB by city+keyword | ✓ SATISFIED | `search_pois.py`: DB-first + Amap fallback, top 10 results with name/rating/tier/coords/highlight_note |
| BIZ-02 | 12-02 | Weather query tool — agent gets weather forecast for city+date range | ✓ SATISFIED | `weather.py` + `amap_service.get_weather()`: live conditions + forecast with travel suggestions |
| BIZ-03 | 12-02 | User preferences tool — reads taste_tags, budget, last 3 itineraries | ✓ SATISFIED | `user_prefs.py`: queries User + ItineraryRow, parses JSON taste_tags, formats Chinese text |
| BIZ-04 | 12-02 | Itinerary context tool — reads current itinerary state | ✓ SATISFIED | `itinerary_context.py`: queries ItineraryRow by id, parses JSON, day-by-day breakdown |
| TOOL-01 | 12-03 | Web search tool — agent can search internet by keywords | ✓ SATISFIED | `web_search.py`: DDGS with cn-zh region, top 5 results, WebSearchProvider protocol |
| TOOL-02 | 12-03 | Web fetch tool — agent can read URL content | ✓ SATISFIED | `web_fetch.py`: httpx + SSRF protection (DNS resolution, IP pinning, redirect validation), 3000-char truncation |
| TOOL-03 | 12-03 | File read/write tool — sandboxed to data/agent_memory/ | ✓ SATISFIED | `file_io.py`: 3 tools (list/read/write), SANDBOX_ROOT, Path.resolve() + is_relative_to() traversal protection |
| TOOL-04 | 12-03 | Command execution tool (reserved, disabled) | ✓ SATISFIED | `command_exec.py`: @function_tool stub returning "暂未开放" message |

No orphaned requirements — all 8 Phase 12 requirement IDs are claimed by plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | No anti-patterns detected in Phase 12 files |

Legacy files (registry.py `return []` on lines 70/77) are Phase 11 code, not modified in Phase 12.

### Human Verification Required

### 1. POI Search Tool End-to-End (BIZ-01)

**Test:** Start the FastAPI server with a seeded DB and valid Amap API key. Call `search_pois` through the SDK Agent with `city="上海"` and `keyword="咖啡馆"`.
**Expected:** Returns formatted Chinese text listing POIs with tier badges (★★★), ratings, coordinates, and highlight_notes for Tier A entries. If DB has <3 matches, Amap API expands results.
**Why human:** Requires running server with seeded database and valid external API key — cannot verify DB query + Amap fallback end-to-end programmatically.

### 2. Weather Tool End-to-End (BIZ-02)

**Test:** Start the server and call `query_weather` through the SDK Agent with `city="上海"` and `days=3`.
**Expected:** Returns formatted weather forecast with current conditions (temperature, weather, humidity, wind) + 3-day forecast with travel suggestions (e.g., "适合户外活动" for sunny days).
**Why human:** Requires valid 高德 API key to call weather endpoint — external service dependency.

### 3. Web Search Tool End-to-End (TOOL-01)

**Test:** Call `web_search` through the SDK Agent with `query="上海小众咖啡馆推荐"`.
**Expected:** Returns top 5 DuckDuckGo results with title, 200-char snippet, and URL in Chinese text format.
**Why human:** External DuckDuckGo API dependency — network call to third-party service. Rate-limited.

### Gaps Summary

No gaps found. All 16 must-have truths are verified against actual codebase. All 8 requirements are satisfied. All 10 tests pass. All key links are wired. The only remaining items are human verification of external API integration — tools that call 高德, DuckDuckGo, or require a seeded database.

---

_Verified: 2026-04-21T01:00:00Z_
_Verifier: the agent (gsd-verifier)_
