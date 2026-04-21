# Feature Landscape: AI Agent Tool Calling System

**Domain:** AI Agent function calling for travel itinerary app (拾途 Shí Tú v1.2)
**Researched:** 2026-04-20
**Context:** Adding agent tool calling to an existing 4-stage pipeline app. Not greenfield — must integrate with existing `DeepSeekClient`, `AmapService`, `EventBus`, and Pydantic models.

---

## Table Stakes

Features users expect from a conversational AI travel assistant. Missing = the AI feels dumb or helpless.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| **Agent loop (tool-call cycle)** | Users ask "帮我找个上海的小众咖啡店" — AI must search POIs, not hallucinate. The core value of agent tools. | Med | `DeepSeekClient`, `AmapService` | Standard OpenAI tool-call loop: send tools → get tool_calls → execute → append result → loop. DeepSeek V3.2 supports this natively. Max iteration guard (e.g., 10 turns). |
| **Tool: POI search** | "找杭州西湖附近的咖啡店" is the #1 use case. Without it, AI is just a chatbot. | Low | `AmapService.search_pois()`, `AmapService.batch_search_pois()` | Wrap existing service. Return: name, address, rating, taste_tags, distance. Already cached in DB via `AmapCache`. |
| **Tool: Weather query** | "明天杭州天气怎么样？带伞吗？" — basic travel question. | Low | New `get_weather()` method or wrap existing if present | Simple API call. Return: temp range, rain probability, UV index, clothing suggestion. |
| **Tool: Route planning** | "从灵隐寺怎么走到北高峰？" — navigation is core to travel. | Low | `AmapService.get_walking_route()` | Already exists. Wrap as tool. Return: distance, duration, polyline for map. |
| **Tool: User preferences** | AI should know "我喜欢文艺风，预算中等" without being told again. | Low | `User.taste_tags_default`, `User.budget_default` from DB | Read-only tool. Inject into system prompt context. NOT a tool the model calls — rather, a tool that returns user profile when asked "我喜欢什么？". |
| **Tool: Itinerary context** | When adjusting, AI needs to know current itinerary state. "把第三天的灵隐寺换成法喜寺" requires knowing Day 3 exists. | Low | Existing `Itinerary`/`ItineraryDay` Pydantic models | Read current itinerary from session. Return structured summary (POIs per day, time slots, notes). |
| **Transparent tool calling** | Users see results ("找到了3家咖啡店"), not the tool mechanics. No JSON schemas or function names in chat. | Low | SSE `EventBus` pattern | Emit `tool_start`/`tool_result` SSE events for frontend loading states. User sees "正在搜索咖啡店..." not `calling search_pois({"keyword": "咖啡店"})`. |
| **Streaming responses** | The existing app streams via SSE. Agent responses must also stream — not block until the entire loop completes. | Med | `DeepSeekClient.stream_chat()`, SSE infrastructure | Stream the LLM's text responses between tool calls. Tool execution itself is fast (sub-second). The final narrative answer streams token by token. |
| **Error handling** | "搜索失败，换个关键词试试？" — graceful degradation when APIs fail. | Low | `tenacity` retry on `AmapService` | Rate limit (429), timeout, no results. Never expose raw error. AI should interpret and suggest alternatives. |
| **Max iteration guard** | Prevent infinite loops where AI keeps calling tools forever. | Low | Agent loop config | Hard cap at 8-10 tool-call rounds per user message. On limit, force final text response. |

---

## Differentiators

Features that set 拾途's agent apart from generic chatbots. Not expected, but directly amplify the core value ("像一个很会玩的本地朋友").

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| **Skills (composable tool packs)** | "杭州探索" skill = POI search + route + food filter. User doesn't pick tools — the AI activates the right skill set based on context. This IS the differentiator. | High | Tool registry, skill definitions | A skill is a named subset of tools + context prompt + example queries. E.g., skill `"杭州咖啡探店"` = `{tools: [search_pois, get_walking_route], context: "杭州精品咖啡场景", examples: ["西湖边安静的咖啡店"]}`. Skills are NOT user-facing — they're internal routing that makes the AI smarter. |
| **Tool: Taste-based POI scoring** | AI doesn't just find POIs — it ranks them by match with user's taste profile. "帮你找到3家咖啡店，按你的喜好排序：第一是你爱的日系风格..." | Med | `filter_pois()` logic (Stage 2), `User.taste_tags_default` | Reuse existing tag-overlap + tier + rating scoring. Expose as a tool that returns scored+ranked results, not raw search. This is what makes it "有品味" vs "有结果". |
| **Tool: Itinerary adjustment** | "把第三天改成更轻松的节奏" — AI reads current itinerary, understands structure, makes targeted changes. Beyond simple chat. | High | Existing adjust pipeline, `AdjustmentPreview` model | The current adjust pipeline works via explicit commands. Agent tool lets AI interpret vague intent ("更轻松") into concrete changes (swap POIs, adjust timing), preview changes, and confirm. |
| **Tool: Nearby discovery** | "我现在在龙翔桥地铁站，附近有什么值得去的？" — location-aware discovery. | Med | Amap nearby search API, user location | Requires `location` parameter (lat/lng). Amap supports `around` search. Returns POIs sorted by distance + taste match. |
| **Skill auto-activation** | AI detects "我想在杭州找好吃的" → auto-activates "杭州美食" skill. User never says "activate skill X". | Med | LLM system prompt, skill registry | Use `tool_choice: "auto"` and inject skill-specific tools into the tools list based on city/intent context. Or include ALL tools and let the model pick — simpler for v1.2. |
| **Tool call progress indicators** | "正在搜索... 找到了3个地方，正在规划路线..." — real-time progress during multi-tool sequences. | Med | SSE `EventBus`, frontend | Emit granular SSE events: `agent_thinking`, `tool_executing(name)`, `tool_completed(name, summary)`. Frontend shows a lightweight progress stepper. Makes multi-tool calls feel fast instead of opaque. |
| **Conversation memory (session-scoped)** | "刚才找到的那家咖啡店，加到行程里" — AI remembers what it found earlier in the conversation. | Low | Message history management | Simply maintain the full message list (user + assistant + tool) within the session. No vector DB needed. Session = one conversation. Clears on new chat. |

---

## Anti-Features

Features to explicitly NOT build for the agent tool system. These are traps that look useful but would waste effort or hurt UX.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **User-facing tool selection UI** | Users don't care about "tools" or "skills". They just want to ask questions. Exposing tool toggles adds complexity without value. | AI selects tools automatically via `tool_choice: "auto"`. Skills are internal routing, not user controls. |
| **Custom tool builder (user-created tools)** | This is a developer platform feature, not a travel app feature. Massive complexity for near-zero MVP value. | Ship with curated tool set. If users want custom tools, that's a v3+ platform play. |
| **MCP (Model Context Protocol) integration** | MCP is for inter-tool orchestration in general AI platforms. 拾途 is a domain-specific app with a fixed set of tools. MCP adds abstraction without benefit. | Direct function calling via OpenAI SDK. Tools are Python functions, not MCP servers. |
| **Multi-agent orchestration** | "Planning agent" + "POI agent" + "weather agent" — adds complexity (inter-agent communication, state sharing) with no benefit for a single-city itinerary. One agent with multiple tools is simpler and better. | Single agent loop with composable tools. If complexity grows, add skills (tool packs), not agents. |
| **Vector DB / RAG for tool results** | Overkill for session-scoped tool memory. The tool results fit in DeepSeek's 128K context window. Vector DB adds infrastructure complexity (embedding service, similarity search) for zero MVP benefit. | Keep full message history in session. DeepSeek V3.2 has 128K context — more than enough for 10+ tool calls + results in one conversation. |
| **Tool result caching (cross-session)** | "上次找的咖啡店" — sounds useful but requires persistent storage, cache invalidation, and session linkage. The POI DB already caches Amap results. | Search again — it's fast (DB cache + Amap cache). If user says "刚才那家", session memory handles it within the same chat. |
| **Streaming tool call arguments** | Showing tool arguments as they stream ("search_pois(keywor...") is a debug feature, not a user feature. It exposes internals and looks broken. | Show human-readable progress: "正在搜索咖啡店..." after the tool call is fully formed. |
| **Agent orchestration frameworks (LangChain, CrewAI, AutoGen)** | These frameworks add layers of abstraction that fight with the existing pipeline architecture. 拾途 already has a pipeline, EventBus, and DeepSeekClient. Adding LangChain means rewriting the world. | Build a lightweight agent loop (~100 lines) using the `openai` SDK's built-in tool calling. No framework needed. The loop is: send tools → execute → append → loop. |
| **Human-in-the-loop tool approval** | "AI wants to search POIs. Approve?" — kills the conversational flow. This is for enterprise agent safety, not travel planning. | Trust the agent with pre-approved tools. All tools are read-only (search, read preferences, calculate routes). No destructive actions to guard against. |
| **Web search tool** | 拾途 is about curated taste, not web scraping. Web search returns generic TripAdvisor/XiaoHongShu results — the opposite of "有品味". | Stick to curated POI database + Amap search. The taste data IS the moat. Web search dilutes it. |

---

## Feature Dependencies

```
Agent Loop (core)
├── Tool: POI search (AmapService)
├── Tool: Route planning (AmapService)
├── Tool: Weather query (new or existing)
├── Tool: User preferences (DB read)
├── Tool: Itinerary context (DB read)
├── Tool: Taste-based POI scoring (Stage 2 logic)
└── Tool: Itinerary adjustment (adjust pipeline)

Skills (composable packs)
├── Depends on: Tool registry
├── Depends on: Agent loop
└── Each skill = subset of tools + context prompt

Streaming agent responses
├── Depends on: Agent loop
├── Depends on: SSE EventBus (existing)
└── Tool progress indicators
    └── Depends on: Streaming responses

Conversation memory
└── Depends on: Agent loop (message history)
    └── No external dependencies

Error handling
└── Depends on: Agent loop (error catching)
    └── Retry via tenacity (existing)
```

**Critical path:** Agent loop → Tool definitions → Tool execution → Streaming integration

---

## MVP Recommendation (v1.2)

### Must-Have (Phase 1 of milestone)
1. **Agent loop** — the core tool-call cycle with max iteration guard
2. **Tool: POI search** — wraps `AmapService.search_pois()`
3. **Tool: Route planning** — wraps `AmapService.get_walking_route()`
4. **Tool: User preferences** — reads `User.taste_tags_default` from DB
5. **Tool: Weather query** — simple weather API wrapper
6. **Streaming responses** — SSE events during agent loop
7. **Error handling** — graceful degradation with retry

### Should-Have (Phase 2 of milestone)
8. **Skills (composable tool packs)** — 2-3 pre-defined skills (e.g., "城市探索", "美食发现")
9. **Tool: Taste-based POI scoring** — reuse `filter_pois()` logic
10. **Tool call progress indicators** — "正在搜索..." SSE events
11. **Conversation memory** — session-scoped message history

### Defer to v1.3+
12. **Tool: Itinerary adjustment** — complex, needs careful integration with adjust pipeline
13. **Tool: Nearby discovery** — requires location input
14. **Skill auto-activation** — can manually route skills in v1.2
15. **Cross-session memory** — overkill for MVP

---

## Complexity Assessment

| Component | Lines of Code (est.) | New Concepts | Risk |
|-----------|---------------------|--------------|------|
| Agent loop | ~100-150 | Tool-call cycle, message management | Low — standard OpenAI pattern |
| Tool definitions (JSON schemas) | ~50-80 per tool | JSON Schema for parameters | Low — Pydantic can auto-generate |
| Tool execution dispatcher | ~50-80 | Tool name → function mapping | Low — dict dispatch |
| SSE event integration | ~30-50 | New event types in EventBus | Low — extend existing pattern |
| Skill definitions | ~20-30 per skill | Skill = tool subset + prompt | Low — data structure, not code |
| Taste-based scoring tool | ~40-60 | Extract from Stage 2 | Med — refactor existing logic into standalone function |
| Itinerary adjustment tool | ~100-150 | Bidirectional sync with pipeline | High — modifying existing pipeline |
| **Total v1.2 MVP** | **~500-700** | | |

---

## Sources

- **DeepSeek Tool Calls docs** — Official API documentation, verified 2026-04-20. OpenAI-compatible format confirmed.
- **OpenAI Python SDK** — `openai` 2.31.0 function calling patterns, `pydantic_function_tool()` helper, streaming tool deltas.
- **openai-cookbook** — Function calling best practices, multi-tool patterns, error handling.
- **Existing 拾途 codebase** — `DeepSeekClient`, `AmapService`, `PipelineCoordinator`, `EventBus`, Pydantic/SQLAlchemy models analyzed for integration points.
