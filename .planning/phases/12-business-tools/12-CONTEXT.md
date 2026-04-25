# Phase 12: Business & General Tools - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement all concrete tools the agent can call — both 拾途 business tools (POI search, weather, user preferences, itinerary context) and general-purpose utilities (web search, web fetch, file I/O, command exec reserved). Also includes the architectural migration from hand-rolled AgentLoop to OpenAI Agents SDK.

Requirements: BIZ-01, BIZ-02, BIZ-03, BIZ-04, TOOL-01, TOOL-02, TOOL-03, TOOL-04.

**Scope expansion:** This phase now also includes migrating from the hand-rolled `AgentLoop`/`ToolRegistry`/`ToolResult` to `openai-agents-python` SDK. This was a Phase 11 artifact but the user decision to adopt the SDK means Phase 12 must handle the migration as a prerequisite.

</domain>

<decisions>
## Implementation Decisions

### Architectural Migration: OpenAI Agents SDK

- **D-01:** Migrate from hand-rolled `AgentLoop` (loop.py), `ToolRegistry` (registry.py), `ToolResult` (result.py) to `openai-agents-python` SDK v0.14+ — replaces ~400 LOC with SDK declarative patterns. `LLMClient` (llm/client.py) is **kept** — pipeline stages (Stage 1-4) continue using `LLMClient.stream_chat()` / `generate_json()` directly. The SDK `Runner` is only used for the agent tool-call loop.
- **D-02:** Use `OpenAIChatCompletionsModel` to wrap DeepSeek's ChatCompletions API — NOT the Responses API (DeepSeek doesn't support it). Construct as: `OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=AsyncOpenAI(api_key=..., base_url="https://api.deepseek.com"))`. The `AsyncOpenAI` client can be shared with the existing `LLMClient`'s internal client or constructed separately.
- **D-03:** Call `set_default_openai_api("chat_completions")` at startup to route all SDK calls through ChatCompletions API
- **D-04:** SDK tools use `@function_tool` decorator — auto-extracts JSON schema from type hints + docstrings, no manual `config.yml` tool definitions needed. The `ctx` parameter (`RunContextWrapper`) is automatically excluded from the tool's JSON schema shown to the LLM.
- **D-05:** `config.yml` tool definitions (from Phase 11) are **retired** — tool schemas come from Python function signatures via SDK introspection. The `config.yml` file itself can be deleted or kept empty.
- **D-06:** **What doesn't work on ChatCompletions path:** `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool`, `ImageGenerationTool`, `ToolSearchTool` — all require Responses API. We build web search and file I/O ourselves.
- **D-07:** Accept SDK dependency weight: `openai-agents-python` v0.14+ (8.3MB, transitive deps: `griffelib`, `mcp`, `requests`, `websockets`, `types-requests`). Add `openai-agents` and `ddgs` to `pyproject.toml` dependencies (project uses pyproject.toml, not requirements.txt).
- **D-08:** `ToolResult` dataclass may be kept as an internal utility if useful, but SDK tools return `str` (text output) by default. Evaluate during implementation.
- **D-08a:** SDK `Runner.run()` has `max_turns` parameter (default 10). Set `max_turns=8` to match our design (Phase 11 D-17).
- **D-08b:** **SSE streaming bridge:** SDK `Runner.run_streamed()` returns `RunResultStreaming` with events (raw_response_event, run_item_stream_event, agent_updated_stream_event). We need to hook into these events to emit `EventBus` events (agent_thinking, tool_executing, tool_completed) for the existing SSE pipeline. Implementation: use SDK `RunHooks` or process streaming events to call `event_bus.emit()`. This is critical for Phase 14 integration — in Phase 12, we validate the basic SDK tool calling works; the SSE bridge can be minimal/deferred to Phase 14.
- **D-08c:** SDK `Agent` constructor requires `model` parameter. Pass `model=OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=deepseek_async_client)` or use `RunConfig.model` override at `Runner.run()` time.

### Tool DI Pattern: RunContextWrapper

- **D-09:** Define `AgentContext` Pydantic model holding request-scoped services: `db_session: AsyncSession`, `amap_service: AmapService`, `user_id: str | None`, `settings: Settings`
- **D-10:** Tools access services via `ctx: RunContextWrapper[AgentContext]` — the `ctx` parameter is the **first** parameter of an `@function_tool` function (e.g., `async def search_pois(ctx: RunContextWrapper[AgentContext], city: str) -> str`). SDK automatically excludes `ctx` from the tool's JSON schema shown to the LLM. Access services as `ctx.context.db_session`, `ctx.context.amap_service`, etc.
- **D-11:** `AgentContext` is constructed per-request in FastAPI dependency injection, passed to `Runner.run(agent, input, context=agent_context)`. When `user_id` is None (unauthenticated), tools that require auth should return a graceful "请先登录" message rather than crashing.

### Web Search (TOOL-01)

- **D-12:** Use `ddgs` package (DuckDuckGo search, free, no API key) for MVP — `pip install ddgs`
- **D-13:** Wrap in a `WebSearchProvider` protocol/ABC for future swap to SerpAPI Baidu or other provider
- **D-14:** Return top 5 results with title + snippet + URL, Chinese query support via `region="cn-zh"`
- **D-15:** Web search is a **fallback tool** — agent uses it when POI DB results are insufficient, not as primary search

### Web Fetch (TOOL-02)

- **D-16:** Use `httpx.AsyncClient` (already in stack) to fetch arbitrary URLs and extract text content
- **D-17:** Truncate fetched content to 3000 chars, include source URL in result
- **D-18:** Block internal/private IPs (prevent SSRF) — reject URLs resolving to 10.x, 172.16-31.x, 192.168.x, localhost

### File I/O (TOOL-03)

- **D-19:** Sandbox to `data/agent_memory/` directory — tools can read/write files within this directory only
- **D-20:** Path traversal protection: resolve to absolute path, verify it starts with sandbox root
- **D-21:** Support operations: list files, read file, write file (create/overwrite)
- **D-22:** File content is UTF-8 text only — no binary files

### Command Exec Reserved (TOOL-04)

- **D-23:** Register a stub tool that always returns "命令执行功能暂未开放" — interface defined but disabled
- **D-24:** Can be enabled via config flag in future phases (no implementation needed now)

### POI Search (BIZ-01)

- **D-25:** Tool wraps existing `AmapService.search_pois()` and DB POI queries — queries DB first (curated data), falls back to Amap API for expansion
- **D-26:** Returns top 10 results max with name, rating, tier, coordinates, highlight_note, taste_tags
- **D-27:** Include "共 N 个结果，显示前 10 个" note when results are truncated

### Weather Query (BIZ-02)

- **D-28:** Add `get_weather(city, days)` method to `AmapService` using 高德 weather API (same API key, free). **Important:** 高德天气 API 的 `city` 参数需要城市编码（adcode），不是城市名。需要一个城市名 → adcode 的映射（可从高德行政区划 API 获取，或在 city config JSON 中维护）。
- **D-29:** 高德 `extensions=all` 返回 `casts` 数组，每天一条预报，字段为 `dayweather`/`nightweather`/`daytemp`/`nighttemp`/`daywind`/`nightwind`/`daypower`/`nightpower`。`extensions=base` 返回实况天气。工具应合并实况 + 预报，返回温度、天气状况、风力、旅行建议。
- **D-30:** No new API key or dependency needed — reuse existing 高德 integration

### User Preferences (BIZ-03)

- **D-31:** Tool reads current user's `taste_tags_default`, `budget_default` from `User` model via DB session. `taste_tags_default` is a JSON string (needs `json.loads`), `budget_default` is a plain string.
- **D-32:** Also reads last 3 itinerary summaries (city + `created_at` dates) for context. Query `ItineraryRow` by `user_id` ordered by `created_at` desc, limit 3. If `user_id` is None (unauthenticated), return empty preferences.
- **D-33:** Read-only — no mutation. Returns structured data for LLM to incorporate into recommendations.

### Itinerary Context (BIZ-04)

- **D-34:** Tool reads current itinerary state from `ItineraryRow` — `city` is a direct column field; POIs and day structure are stored in `parsed_itinerary` as a JSON string (needs `json.loads`). The parsed structure is `{"title": ..., "days": [{"day": 1, "pois": [...]}], ...}`.
- **D-35:** Used during itinerary generation or adjustment to give agent context about what's already planned. The tool needs an `itinerary_id` parameter to identify which itinerary to read.

### Result Size Budgets

- **D-36:** POI search: top 10 results with truncation note
- **D-37:** Weather: full forecast (typically 3-7 days, small payload, no truncation needed)
- **D-38:** Web search: top 5 results (title + 200-char snippet + URL)
- **D-39:** Web fetch: 3000 chars max, include source URL
- **D-40:** User preferences: full profile (small payload, no truncation)
- **D-41:** Itinerary context: full current itinerary (structured, moderate size)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### SDK & Architecture
- OpenAI Agents SDK tools docs: https://openai.github.io/openai-agents-python/zh/tools/ — `@function_tool`, `RunContextWrapper`, `FunctionTool`
- OpenAI Agents SDK streaming docs: https://openai.github.io/openai-agents-python/zh/streaming/ — `Runner.run_streamed()`, streaming events
- OpenAI Agents SDK context docs: https://openai.github.io/openai-agents-python/zh/context/ — `RunContextWrapper`, context types
- `agents.models.openai_chatcompletions.OpenAIChatCompletionsModel` — ChatCompletions model adapter (import verified: `from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel`)
- `agents.set_default_openai_api` — API routing function (import verified)
- `.planning/research/STACK.md` — Stack additions (now includes `openai-agents-python`, `ddgs`)
- `.planning/REQUIREMENTS.md` — v1.2 requirements BIZ-01~04, TOOL-01~04 (Phase 12 scope)

### Existing Code (to migrate from / integrate with)
- `src/backend/agent/loop.py` — Current AgentLoop (to be replaced by SDK `Runner`)
- `src/backend/tools/registry.py` — Current ToolRegistry (to be replaced by SDK tool registration)
- `src/backend/tools/result.py` — ToolResult (may be kept as utility or retired)
- `config.yml` — Current tool definitions (to be retired in favor of `@function_tool` decorators)
- `src/backend/api/dependencies.py` — FastAPI DI (update to construct `AgentContext`)
- `src/backend/services/amap_service.py` — AmapService (add `get_weather()` method, reuse for POI search)
- `src/backend/models/database.py` — User, POI, ItineraryRow models (tools query these)

### Prior Phase Decisions
- `.planning/phases/11-agent-framework-core/11-CONTEXT.md` — Phase 11 decisions (some superseded by SDK migration)

</canonical_refs>

<code_context>
## Existing Code Insights

### To Be Replaced (Phase 11 artifacts)
- `src/backend/agent/loop.py` (256 LOC) — `AgentLoop` with `run()` and `run_streaming()`, `ToolExecutor` type alias, max iteration guard, SSE event emission
- `src/backend/tools/registry.py` (99 LOC) — `ToolRegistry` loading from `config.yml`, `get_openai_tools()` conversion
- `config.yml` (16 LOC) — Single tool definition (`search_pois`)
- `src/backend/api/dependencies.py` lines 35-46 — `get_tool_registry()` and `get_agent_loop()` DI providers

### To Be Kept / Extended
- `src/backend/llm/client.py` — `LLMClient` stays (used by pipeline stages that don't need agent tools)
- `src/backend/services/amap_service.py` — Add `get_weather()` method
- `src/backend/models/database.py` — User, POI, ItineraryRow queried by tools
- `src/backend/api/dependencies.py` — Update DI to construct `AgentContext`, provide SDK `Agent`

### Established Patterns (still valid)
- Services are request-scoped — `AmapService` created per-request with DB session
- `httpx.AsyncClient` for external API calls with `tenacity` retry
- FastAPI `Depends()` injection pattern
- SSE via `StreamingResponse` + `EventBus` (pipeline stages)
- Pydantic models for all structured data

### New Files to Create
- `src/backend/agent/context.py` — `AgentContext` Pydantic model
- `src/backend/tools/search_pois.py` — BIZ-01 tool
- `src/backend/tools/weather.py` — BIZ-02 tool
- `src/backend/tools/user_prefs.py` — BIZ-03 tool
- `src/backend/tools/itinerary_context.py` — BIZ-04 tool
- `src/backend/tools/web_search.py` — TOOL-01 tool
- `src/backend/tools/web_fetch.py` — TOOL-02 tool
- `src/backend/tools/file_io.py` — TOOL-03 tool
- `src/backend/tools/command_exec.py` — TOOL-04 tool (stub)

</code_context>

<specifics>
## Specific Ideas

- `AgentContext` is a Pydantic BaseModel (not a dict) — enables type checking and validation at SDK boundary
- 高德 weather API endpoint: `https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=all` — `city` param requires **adcode** (城市编码), NOT city name. E.g., 上海 adcode = "310000", 杭州 adcode = "330100". Maintain a mapping in city config JSON (`data/cities/*.json`) or add an `adcode` field to `CityConfig`.
- `ddgs` package: `from ddgs import DDGS; results = DDGS().text("上海 咖啡馆", region="cn-zh", max_results=5)`
- SSRF protection for web fetch: use `ipaddress.ip_address()` on resolved hostname, reject private ranges
- File I/O sandbox: `data/agent_memory/` directory does not exist yet — must be created during Phase 12 implementation (either via Alembic migration, startup script, or first-access creation). Each user gets a subdirectory (`data/agent_memory/{user_id}/`)
- `ItineraryRow.parsed_itinerary` is a JSON string — tools must `json.loads()` to access day/POI structure

</specifics>

<deferred>
## Deferred Ideas

- SerpAPI Baidu migration (when DDG Chinese quality proves insufficient)
- Tool result caching (cross-session, AGENT-06 in v1.3)
- Command execution enablement (TOOL-04 stays disabled)
- Nearby discovery tool (TOOL-05 in v1.3)
- Taste-based POI scoring tool (TOOL-06 in v1.3)

</deferred>

---

*Phase: 12-business-tools*
*Context gathered: 2026-04-20*
