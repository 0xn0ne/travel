# Requirements: 拾途 (Shí Tú) — v1.2

**Defined:** 2026-04-20
**Core Value:** 帮你发现你会喜欢但自己找不到的地方，并且用对的方式推荐给你——品味数据 + SOUL 提示词的组合，让行程有"本地朋友推荐"的温度

## v1.2 Requirements

Requirements for AI Agent Tool System milestone. Each maps to roadmap phases.

### Agent Framework

- [ ] **AGENT-01**: Agent loop implements tool-call cycle — send tools + messages to LLM, LLM decides whether to call tools, execute tool functions, append results, loop until LLM responds with final text or max iterations reached
- [x] **AGENT-02**: Tool registry supports dynamic registration — tools register with name, description, Pydantic input schema; registry validates and exposes tools to agent loop
- [ ] **AGENT-03**: Agent loop streams tool-call progress via SSE events — `agent_thinking` (LLM processing), `tool_executing` (tool name + args), `tool_completed` (result summary) — transparent to user, no tool mechanics in final response
- [ ] **AGENT-04**: Max iteration guard (8 rounds per message) — agent stops with graceful message if limit reached; tool errors are caught and returned as error context to LLM for recovery

### General Tools

- [ ] **TOOL-01**: Web search tool — agent can search the internet by keywords (e.g., "上海 清凉 避暑 咖啡馆") as fallback when POI DB search fails or returns insufficient results; returns top results with title + snippet + URL
- [ ] **TOOL-02**: Web fetch tool — agent can read and extract text content from a given URL; used to get detailed info from search results (e.g., blog posts about a restaurant)
- [ ] **TOOL-03**: File read/write tool — agent can read from and write to a designated directory (e.g., `data/agent_memory/`); used for checkpoint saves, long-term memory (user habits, preferences, trip notes); cannot access paths outside the designated directory
- [ ] **TOOL-04**: Command execution tool (reserved) — interface defined and registered but **disabled by default**; can be enabled via config flag; when disabled, returns "command execution is not available" message

### 拾途 Business Tools

- [ ] **BIZ-01**: POI search tool — agent searches POI database by city + keyword/category via existing AmapService and DB queries; returns name, rating, tier, coordinates, highlight_note
- [ ] **BIZ-02**: Weather query tool — agent gets weather forecast for a city and date range via Amap weather API; returns temperature, conditions, suggestions
- [ ] **BIZ-03**: User preferences tool (read-only) — agent reads current user's taste_tags, budget_default, and past itinerary history from User model
- [ ] **BIZ-04**: Itinerary context tool — agent reads current itinerary state (POIs, day structure, city, dates) for context-aware tool calls during generation or adjustment

### Skill System

- [ ] **SKILL-01**: Skill = named composable tool pack — each skill defines: name, description, subset of registered tools, context prompt (system instructions), example queries; loaded from JSON/YAML config files in `data/skills/`
- [ ] **SKILL-02**: Skill auto-activation — when user message or pipeline stage matches a skill's trigger conditions (keywords, city, topic), the skill is activated: its tools are enabled and context prompt is injected into the agent's system message
- [ ] **SKILL-03**: Pre-built skills shipped with app — "行程规划" (POI search + weather + route + preferences + write checkpoint), "美食探索" (POI search + web search + preferences), "本地人推荐" (POI search + web search + web fetch); users cannot create custom skills via UI

### Memory & Context

- [ ] **MEM-01**: SQLite-based agent memory — new `agent_memories` table stores structured entries: user_id, key (e.g., "preference_coffee", "checkpoint_shanghai_day2"), value (JSON), created_at, updated_at
- [ ] **MEM-02**: Agent reads relevant memories at conversation start — loads user preferences, recent checkpoints, trip notes; writes new memories during conversation when user shares preferences or reaches milestones
- [ ] **MEM-03**: Memory is scoped per-user — agent only accesses memories of the authenticated user; unauthenticated sessions have no persistent memory

### Pipeline Integration

- [ ] **PIPE-01**: New Agent Stage added to existing pipeline — inserted between Stage 2 (pre-filter) and Stage 3 (LLM+SOUL); agent receives filtered POI candidates + user intent, uses tools to enrich data (web search fallback, weather check, nearby discovery), passes enriched context to Stage 3
- [ ] **PIPE-02**: Agent Stage streams tool-call progress via existing SSE pipeline — reuses EventBus with new event types, frontend displays progress messages like "正在搜索附近好去处..."

### Chat Integration

- [ ] **CHAT-01**: Chat API endpoint — `POST /api/chat` accepts user message + optional session_id; agent processes message with tool calling, returns streaming response via SSE with final text answer
- [ ] **CHAT-02**: Chat frontend UI — floating chat bubble or side panel in itinerary view; user types message, sees streaming AI response; tool calls are transparent (user only sees final answer)
- [ ] **CHAT-03**: Session-scoped conversation — messages stored in `chat_messages` table (SQLite); agent receives last N messages as context; new session starts fresh unless user continues existing session

## v1.3 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Advanced Agent

- **AGENT-05**: Multi-agent orchestration — specialized agents for different tasks (POI researcher, itinerary optimizer, local culture expert)
- **AGENT-06**: Tool result caching (cross-session) — cache frequently queried POI/weather results in Redis

### Advanced Tools

- **TOOL-05**: Nearby discovery tool — find POIs around a given lat/lng within radius
- **TOOL-06**: Taste-based POI scoring tool — score POIs by user taste alignment
- **TOOL-07**: Itinerary adjustment tool — modify existing itinerary via agent (add/remove/reorder POIs)

### Advanced Memory

- **MEM-04**: Conversation summarization — long conversations auto-summarized to save context window
- **MEM-05**: Cross-trip learning — agent learns from past trips to improve future recommendations

## Out of Scope

| Feature | Reason |
|---------|--------|
| 用户自建工具 UI | 过度复杂，非核心 |
| MCP 协议集成 | 标准尚未成熟，不依赖 |
| Vector DB / RAG | MVP 不需要语义搜索，SQLite 结构化存储足够 |
| LangChain / CrewAI / AutoGen | 过度抽象，手写 agent loop 更简单可控 |
| 人机审批工具调用 | MVP 工具都是只读/安全的，不需要审批 |
| 多语言支持 | 目标用户为中国用户 |
| Agent 框架选择器 | 单一 hand-rolled 方案，不需要切换框架 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGENT-01 | Phase 11 | Pending |
| AGENT-02 | Phase 11 | Complete (11-01) |
| AGENT-03 | Phase 14 | Pending |
| AGENT-04 | Phase 11 | Pending |
| TOOL-01 | Phase 12 | Pending |
| TOOL-02 | Phase 12 | Pending |
| TOOL-03 | Phase 12 | Pending |
| TOOL-04 | Phase 12 | Pending |
| BIZ-01 | Phase 12 | Pending |
| BIZ-02 | Phase 12 | Pending |
| BIZ-03 | Phase 12 | Pending |
| BIZ-04 | Phase 12 | Pending |
| SKILL-01 | Phase 13 | Pending |
| SKILL-02 | Phase 13 | Pending |
| SKILL-03 | Phase 13 | Pending |
| MEM-01 | Phase 13 | Pending |
| MEM-02 | Phase 13 | Pending |
| MEM-03 | Phase 13 | Pending |
| PIPE-01 | Phase 14 | Pending |
| PIPE-02 | Phase 14 | Pending |
| CHAT-01 | Phase 15 | Pending |
| CHAT-02 | Phase 15 | Pending |
| CHAT-03 | Phase 15 | Pending |

**Coverage:**
- v1.2 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

**Phase distribution:**
- Phase 11 (Agent Framework Core): 3 requirements
- Phase 12 (Business & General Tools): 8 requirements
- Phase 13 (Memory & Skills): 6 requirements
- Phase 14 (Pipeline Integration): 3 requirements
- Phase 15 (Chat Integration): 3 requirements

---
*Requirements defined: 2026-04-20*
*Last updated: 2026-04-20 — v1.2 roadmap created, 23/23 requirements mapped*
