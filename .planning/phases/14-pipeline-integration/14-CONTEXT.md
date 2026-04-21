# Phase 14: Pipeline Integration - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent enriches itinerary generation by using tools to gather real-time data, with visible progress streamed to the user. A new Agent Stage runs between Stage 2 (pre-filter) and Stage 3 (LLM+SOUL), receiving filtered POI candidates + user intent, using tools to enrich data, and passing enriched context to Stage 3.

Requirements: PIPE-01, PIPE-02, AGENT-03.

**In scope:**
- New `agent_enrich()` async function inserted between Stage 2 and Stage 3
- SDK Agent + ALL_TOOLS (12 tools) running during pipeline execution
- SSE progress events for tool calls (agent_thinking, tool_executing, tool_completed)
- Agent output as enrichment text injected into Stage 3 prompt
- EventBus integration for streaming agent progress
- Skill-aware instructions via `build_agent_instructions()`

**Out of scope:**
- Chat UI (Phase 15)
- Chat API endpoint (Phase 15)
- chat_messages table (Phase 15)
- Frontend changes (existing SSE consumer handles all stages)
- Adjust pipeline agent integration (future enhancement)

</domain>

<decisions>
## Implementation Decisions

### Agent Stage Architecture (PIPE-01)

- **D-01:** New `agent_enrich()` async function in `src/backend/pipeline/stages/stage_agent.py`, following existing stage pattern (independent async function, not a class).
- **D-02:** Coordinator calls `agent_enrich()` between `filter_pois()` and `generate_itinerary()` in `_run_pipeline_async()`.
- **D-03:** `agent_enrich()` receives: `llm_client`, `intent` (IntentOutput), `poi_candidates` (list[POICandidate]), `user_input` (str), `event_bus` (EventBus), and `agent_context` (AgentContext with db_session, amap_service, user_id, settings).
- **D-04:** Uses SDK `Runner.run()` with the cached Agent from `get_sdk_agent()` (12 tools), overriding `instructions` with `build_agent_instructions(user_input, intent.interests)` for per-request skill injection.
- **D-05:** Agent's system prompt includes: current city, user intent summary, count of POI candidates available, instruction to enrich (not replace) the data.
- **D-06:** Agent runs with `max_turns=8` (per Phase 11 D-08a). If max turns reached, return whatever enrichment was gathered so far (graceful degradation, not error).

### SSE Progress Events (PIPE-02, AGENT-03)

- **D-07:** Three SSE event types emitted via existing EventBus during agent tool calls:
  - `agent_thinking` — emitted when LLM starts processing. Stage="agent", status="thinking", message="正在思考..." or similar Chinese text.
  - `tool_executing` — emitted before tool execution. Stage="agent", status="executing", message=human-readable Chinese description (e.g., "正在搜索上海附近的好去处..."). Tool name and raw arguments NEVER exposed.
  - `tool_completed` — emitted after tool returns. Stage="agent", status="completed", message=result summary in Chinese (e.g., "找到了3个新地点").
- **D-08:** Each tool call produces exactly 1 `tool_executing` + 1 `tool_completed` event pair. `agent_thinking` emitted once at the start of the agent stage.
- **D-09:** Tool-call mechanics (JSON schemas, function names, raw arguments) are NEVER in user-facing SSE. Only human-readable Chinese messages.
- **D-10:** SSE events use existing `PipelineEvent` dataclass with `stage="agent"`. No new event classes needed.

### Data Handoff to Stage 3 (PIPE-01)

- **D-11:** Agent output is an enrichment text string (Chinese), NOT a modified POI list. The agent describes additional context it discovered: weather conditions, nearby discoveries, user preference insights from memory, web search findings.
- **D-12:** Stage 3 (`generate_itinerary`) receives a new optional parameter `enrichment_context: str | None = None`. When present, the enrichment text is appended to the user message in the SOUL prompt as an additional section (e.g., "## 智能补充信息\n{enrichment_context}").
- **D-13:** POI candidates list passed to Stage 3 is NOT modified by the agent stage. Agent only produces supplementary text context.
- **D-14:** If agent stage fails or times out, pipeline continues with `enrichment_context=None` — Stage 3 works exactly as before. Agent enrichment is non-blocking.

### Pipeline Coordinator Changes

- **D-15:** `PipelineCoordinator.__init__` gains optional `agent_context: AgentContext | None = None` parameter. When None, agent stage is skipped (backward compatible).
- **D-16:** Coordinator emits `PipelineEvent(stage="agent", status="started", ...)` before agent runs and `PipelineEvent(stage="agent", status="complete", ...)` after agent completes.
- **D-17:** SSE event flow for full pipeline: intent → prefilter → agent → generation → validation. Existing frontend handles new "agent" stage transparently.

### SSE Event Hookup

- **D-18:** The agent stage needs a callback mechanism to emit SSE events during tool calls. Two approaches:
  - Option A: Wrap the SDK Runner's tool execution with a custom hook that emits events via EventBus.
  - Option B: Create a helper that the `agent_enrich()` function calls before/after each tool invocation.
- **D-19:** Since SDK `Runner.run()` manages the tool-call loop internally, the cleanest approach is to intercept at the tool level: create wrapper functions that emit `tool_executing`/`tool_completed` events around each `@function_tool` call, OR use a custom `AgentHook` if the SDK supports it.
- **D-20:** The executor should investigate SDK hooks/callbacks for tool execution interception. If SDK doesn't support hooks, wrap tool functions with event-emitting decorators.

### Agent's Discretion

- Exact Chinese messages for each event type
- How to format the agent's system prompt (what POI info to include, what instructions to give)
- Whether to use SDK hooks or tool wrappers for SSE emission
- Exact enrichment text format and length limits
- How to handle agent errors gracefully

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pipeline Architecture
- `.planning/ROADMAP.md` §Phase 14 — Pipeline Integration success criteria
- `.planning/REQUIREMENTS.md` §PIPE-01, PIPE-02, AGENT-03 — Requirements
- `src/backend/pipeline/coordinator.py` — 4-stage pipeline orchestration, event emission pattern
- `src/backend/pipeline/events.py` — EventBus, PipelineEvent dataclass
- `src/backend/pipeline/stages/stage3_generate.py` — Stage 3 (receives enrichment context)

### Agent System (from prior phases)
- `.planning/phases/12-business-tools/12-CONTEXT.md` — SDK Agent, ALL_TOOLS, AgentContext, DI patterns
- `.planning/phases/13-memory-skills/13-CONTEXT.md` — Skill system, build_agent_instructions(), memory tools
- `src/backend/agent/loop.py` — AgentLoop (reference for SSE event patterns, may be retired)
- `src/backend/api/dependencies.py` — get_sdk_agent(), build_agent_instructions(), get_agent_context()

### SSE Infrastructure
- `src/backend/api/routes/stream.py` — SSE endpoint, event subscription pattern
- `src/backend/api/routes/generate.py` — Pipeline trigger, active_pipelines dict

### Prior Phase Decisions
- `.planning/phases/11-agent-framework-core/11-CONTEXT.md` — AgentLoop, SSE events, max_turns=8
- `src/backend/tools/__init__.py` — ALL_TOOLS (12 functions)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **PipelineEvent + EventBus**: Fully functional SSE event system. Agent stage reuses `PipelineEvent(stage="agent", ...)` — no new classes needed.
- **SDK Agent (get_sdk_agent)**: lru_cache'd singleton with 12 tools. Agent stage calls `Runner.run()` with this agent, overriding instructions per-request.
- **build_agent_instructions()**: Skill-aware instruction builder from Phase 13. Ready to use for per-request prompt injection.
- **ALL_TOOLS**: 12 @function_tool functions (POI search, weather, web search, memory, etc.) — all available to agent stage.
- **Stream endpoint**: SSE consumer in `stream.py` handles any `PipelineEvent` with `stage="agent"` — no frontend changes needed.

### Established Patterns
- **Stage pattern**: Each stage is an independent async function called by coordinator. Stages receive needed services as parameters (llm_client, db, amap_service).
- **Event emission**: Coordinator emits `PipelineEvent` before and after each stage with human-readable Chinese messages.
- **LLM calls**: Stages use `llm_client.generate_json()` for structured output, `llm_client.stream_chat()` for streaming.
- **Error handling**: Stages catch exceptions and emit error events before re-raising.

### Integration Points
- **coordinator._run_pipeline_async()**: Insert `agent_enrich()` call between `filter_pois()` and `generate_itinerary()`. Add agent SSE events around the call.
- **stage3_generate.py**: Add `enrichment_context` parameter. Append to user message in the SOUL prompt template.
- **PipelineCoordinator.__init__**: Add optional `agent_context` parameter for DI.
- **generate route**: Where coordinator is instantiated — needs to pass AgentContext.

</code_context>

<specifics>
## Specific Ideas

- Agent should feel like "a knowledgeable local friend quickly checking a few things before planning your trip" — not a long, silent pause
- SSE messages should be warm and specific: "正在查看上海的天气..." not generic "processing..."
- Agent enrichment should enhance the SOUL prompt's quality, not replace it — the SOUL prompt remains the primary creative voice
- The agent stage should add ~5-15 seconds to total pipeline time (acceptable if user sees meaningful progress)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-pipeline-integration*
*Context gathered: 2026-04-21*
