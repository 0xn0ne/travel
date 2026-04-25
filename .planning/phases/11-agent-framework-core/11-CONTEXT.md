# Phase 11: Agent Framework Core - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Core agent loop that receives messages, decides whether to call tools via LLM function calling, executes them, and returns results. Includes tool registry with centralized config, max iteration guard, and error recovery. This is the foundation that all subsequent phases (tools, skills, chat) depend on.

Requirements: AGENT-01 (agent loop), AGENT-02 (tool registry), AGENT-04 (iteration guard + error recovery).

</domain>

<decisions>
## Implementation Decisions

### LLM Client Architecture
- **D-01:** Create new `LLMClient` class replacing `DeepSeekClient` entirely — delete the old class and migrate all call sites (`PipelineCoordinator`, `ChatGPTClient` reference chain, `generate.py`, `adjust_pipeline`, test runner, all stage files)
- **D-02:** `LLMClient` supports three modes: (1) streaming chat (`stream_chat`), (2) JSON generation (`generate_json`), (3) tool-calling chat (`tool_chat`) — the new method that sends tools + messages and returns either a tool_calls response or a final text response
- **D-03:** `LLMClient` remains model-agnostic via OpenAI SDK `AsyncOpenAI` — `base_url` and `model` are configurable (currently DeepSeek, but any OpenAI-compatible endpoint works)

### Agent Loop Design
- **D-04:** New `AgentLoop` class, independent from `LLMClient` — holds a tool registry + references `LLMClient` for LLM calls
- **D-05:** `AgentLoop` is generic/reusable — same class works for both pipeline Stage integration (Phase 14) and chat endpoint (Phase 15)
- **D-06:** Core loop: `run(messages, tools) → final_text_response` — sends messages + available tools to LLM, if LLM returns tool_calls then execute tools, append results, loop; if LLM returns text, that's the final response
- **D-07:** Non-streaming tool calls — wait for complete LLM response before executing tools (DeepSeek function calling is more stable in non-streaming mode)
- **D-08:** Final text response from the agent IS streamed token-by-token via `stream_chat` — only the tool-call decision phase is non-streaming

### Tool Registry
- **D-09:** Tool definitions centralized in a single `config.yml` in project root — contains all tool schemas (name, description, parameters in JSON Schema format)
- **D-10:** Python tool implementations live in `src/backend/tools/` — each tool is a Python function that takes validated Pydantic input and returns a `ToolResult`
- **D-11:** `ToolRegistry` class loads tool definitions from `config.yml`, maps tool names to Python functions, validates inputs via Pydantic, and converts definitions to OpenAI function calling format
- **D-12:** Tool registration is static at startup — load from config, no dynamic registration at runtime (dynamic loading is for Skills in Phase 13)

### Tool Output Format
- **D-13:** All tools return a unified `ToolResult` class with three fields: `data` (the actual result, any type), `error` (error message if failed, None if success), `summary` (human-readable Chinese summary for SSE display)
- **D-14:** Large results (e.g., POI search returning many results) are truncated before sending to LLM — tool implementation handles truncation, returns top N results with a note like "显示前10个结果，共25个"

### Error Handling
- **D-15:** Tool errors are fed back to the LLM as tool result messages with error context — the LLM decides whether to retry with different parameters, use a different tool, or inform the user
- **D-16:** No automatic retry at the agent loop level — individual tools may use `tenacity` internally (like existing `AmapService`), but the loop itself does not retry failed tool calls
- **D-17:** Max iteration guard: after 8 tool-call rounds, inject a system message: "已达到最大工具调用次数，请基于已有信息生成最终回答" and force one final LLM call with no tools available
- **D-18:** Network-level errors (timeout, rate limit) on the LLM call itself are handled by `tenacity` retry in `LLMClient` (inherited from existing `DeepSeekClient` pattern)

### SSE Event Design
- **D-19:** Three new event types via existing `EventBus` and `PipelineEvent`: `agent_thinking` (LLM processing, no tool call yet), `tool_executing` (tool name + human-readable summary of what it's doing), `tool_completed` (result summary)
- **D-20:** All SSE events contain only human-readable Chinese messages — tool names, JSON schemas, and function arguments never appear in user-facing SSE stream
- **D-21:** Agent SSE events use `stage="agent"` to coexist with existing pipeline stages (`intent`, `prefilter`, `generation`, `validation`)

### FastAPI Integration
- **D-22:** `AgentLoop` is provided via FastAPI dependency injection — new `get_agent_loop()` dependency in `dependencies.py`, similar to existing `get_llm_client()`
- **D-23:** `AgentLoop` dependency receives `LLMClient`, `ToolRegistry`, and optional `EventBus` via injection

### the agent's Discretion
- Exact Pydantic models for tool inputs (specific field names, validation rules)
- Internal structure of `ToolRegistry` class (dict vs ordered dict, lookup performance)
- How `LLMClient.tool_chat()` handles the response object parsing
- Exact config.yml schema for tool definitions
- Error message formatting in ToolResult

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Agent Tool System Design
- `.planning/research/FEATURES.md` — Feature landscape: table stakes, differentiators, anti-features, feature dependencies
- `.planning/research/STACK.md` — Stack additions (OpenAI SDK function calling, no new dependencies)
- `.planning/REQUIREMENTS.md` — v1.2 requirements AGENT-01, AGENT-02, AGENT-04 (Phase 11 scope)
- `.planning/ROADMAP.md` — Phase 11 goal, success criteria, dependency chain

### Existing Architecture (MUST understand before implementing)
- `src/backend/llm/client.py` — Current `DeepSeekClient` to be replaced (streaming, JSON, retry patterns)
- `src/backend/pipeline/coordinator.py` — `PipelineCoordinator` that uses LLM client (all call sites to migrate)
- `src/backend/pipeline/events.py` — `EventBus` and `PipelineEvent` (SSE infrastructure to extend)
- `src/backend/api/dependencies.py` — FastAPI dependency injection (pattern to follow)
- `src/backend/api/routes/generate.py` — Generate route using `PipelineCoordinator` (integration point)
- `src/backend/config.py` — `Settings` class (config pattern to extend)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AsyncOpenAI` client (openai==2.31.0): Already installed, supports `tools` parameter in `chat.completions.create()` natively
- `EventBus` fan-out pattern: Clean pub/sub for SSE — just emit new event types, no infrastructure changes needed
- `PipelineEvent` dataclass: Extendable — add new `event_type` values for agent events
- `tenacity` retry decorator: Already used in `DeepSeekClient`, reuse in `LLMClient`
- FastAPI `Depends()` injection: Established pattern in `dependencies.py` — add `get_agent_loop()`, `get_llm_client()` (updated)

### Established Patterns
- Services are request-scoped (not singletons) — `AmapService` created per-request with DB session
- LLM client is a module-level singleton via `lru_cache` — `get_llm_client()` in dependencies
- SSE streaming via `StreamingResponse` + `asyncio.Queue` — established in `generate.py`
- Pydantic models for all structured data — `models/pydantic.py`

### Integration Points
- `src/backend/llm/client.py` — Replace `DeepSeekClient` with `LLMClient`
- `src/backend/api/dependencies.py` — Add `get_agent_loop()`, update `get_llm_client()` to return `LLMClient`
- `src/backend/pipeline/coordinator.py` — Migrate from `DeepSeekClient` to `LLMClient` (lines 19, 109, 314)
- `src/backend/api/routes/generate.py` — Update imports, dependency injection
- `src/backend/api/routes/test_runner.py` — May reference `DeepSeekClient`
- All 4 pipeline stage files — Import `LLMClient` instead of `DeepSeekClient`

</code_context>

<specifics>
## Specific Ideas

- Config file in project root (`config.yml`) for tool definitions — consistent with project's data-in-root, code-in-src pattern
- `ToolResult` with summary field is key — enables clean SSE messages without tool internals leaking to user
- Agent SSE events use `stage="agent"` namespace to avoid collision with existing pipeline stages

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-agent-framework-core*
*Context gathered: 2026-04-20*
