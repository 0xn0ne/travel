# Phase 15: Chat Integration - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Chat API endpoint + frontend floating chat bubble + session-scoped (authenticated) or ephemeral (anonymous) conversations. Agent processes user messages with full tool access (12 tools), returns streaming response via SSE. Users see final answer with tool progress indicators; tool mechanics are hidden.

Requirements: CHAT-01, CHAT-02, CHAT-03.

**In scope:**
- `POST /api/chat` endpoint accepting user message + optional session_id
- `chat_messages` DB table for authenticated user conversations
- SDK Agent with ALL_TOOLS processing chat messages
- SSE streaming response reusing PipelineEvent pattern
- Floating chat bubble component on frontend
- Agent receives last 10 messages as context (authenticated users)
- Anonymous chat: ephemeral, in-memory, no DB writes
- Authenticated chat: messages persisted, memory tools active

**Out of scope:**
- Chat history list / session management UI (no session history — memory tools handle persistence)
- Multi-agent conversations
- Chat in adjust pipeline (existing adjust uses its own flow)
- Real-time collaboration
- File/image attachments in chat

</domain>

<decisions>
## Implementation Decisions

### Chat API (CHAT-01)

- **D-01:** New `POST /api/chat` endpoint in `src/backend/api/routes/chat.py`. Accepts `{ message: str, session_id?: str }`. Returns SSE `StreamingResponse` identical to generate endpoint pattern.
- **D-02:** Uses SDK `Runner.run()` with cached Agent from `get_sdk_agent()`, overriding `instructions` with `build_agent_instructions(message)`.
- **D-03:** Agent runs with `max_turns=8` (same as pipeline agent stage).
- **D-04:** SSE events reuse `PipelineEvent` dataclass with `stage="chat"`. Event types: `chat_thinking`, `tool_executing`, `tool_completed`, `chat_text` (streaming answer chunks), `done`.
- **D-05:** Tool calls emit human-readable Chinese progress events via `PipelineSSEHooks` (reuse from Phase 14). Tool mechanics never exposed.
- **D-06:** Final agent text streamed as `chat_text` events (chunked for typewriter effect), terminated by `done` event.

### Chat Frontend (CHAT-02)

- **D-07:** Floating chat bubble component in bottom-right corner, overlaying all pages. Positioned fixed, appears on click.
- **D-08:** Chat bubble contains: message list area, text input, send button. Messages show `ChatMessage { role: 'user' | 'assistant', text: string }`.
- **D-09:** Agent responses show typing indicator during `chat_thinking` / `tool_executing` events, then typewriter-style text rendering during `chat_text` events.
- **D-10:** Uses `useSSE` composable (existing) to connect to `POST /api/chat`. SSE event handling reuses existing patterns from generate/adjust.
- **D-11:** Bubble component registered in `App.vue` so it appears on all pages (not route-specific).
- **D-12:** No session history list UI. Important data (preferences, trip context) persists via agent memory tools, not chat history. Each conversation is self-contained.

### Conversation Persistence (CHAT-03)

- **D-13:** `chat_messages` table: `id` (UUID), `user_id` (FK to users, nullable for future), `role` ('user' | 'assistant'), `content` (TEXT), `session_id` (UUID string), `created_at` (datetime). Composite index on `(user_id, session_id, created_at)`.
- **D-14:** Authenticated users: messages written to `chat_messages` after each turn. Agent receives last 10 messages from current session as conversation context.
- **D-15:** Anonymous users: ephemeral in-memory only. No DB writes. No conversation history. Last 10 messages kept in a request-scoped list (not persisted). Memory tools return empty for anonymous.
- **D-16:** `session_id` generated client-side (UUID v4) on first chat open. Included in every request. New session = new UUID. No server-side session creation.
- **D-17:** No session expiry cleanup needed — user explicitly said no session history. Memory tools handle long-term persistence via `agent_memories` table (Phase 13).
- **D-18:** `chat_messages` table has no explicit TTL or cleanup job. Messages are append-only for authenticated users. If cleanup needed later, add separately.

### Agent Context

- **D-19:** For authenticated users: `AgentContext` created with `db_session`, `amap_service`, `user_id`, `settings`, `active_skills=[]`. Memory and preference tools work normally.
- **D-20:** For anonymous users: `AgentContext` created with `user_id=None`. Tools that require auth (memory, preferences, itinerary context) return empty/error gracefully. Search, weather, web tools still work.
- **D-21:** Agent instructions for chat include: "你是一个旅行助手拾途" + matched skill prompts (via `build_agent_instructions()`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Agent System
- `src/backend/agent/context.py` — AgentContext Pydantic model, create_deepseek_model()
- `src/backend/api/dependencies.py` — get_sdk_agent(), build_agent_instructions(), PipelineSSEHooks import
- `src/backend/pipeline/stages/stage_agent.py` — PipelineSSEHooks (reuse for chat), agent_enrich() as reference pattern

### SSE Infrastructure
- `src/backend/pipeline/events.py` — EventBus, PipelineEvent, emit/subscribe/done pattern
- `src/backend/api/routes/generate.py` — SSE StreamingResponse pattern to replicate for chat
- `src/frontend/src/composables/useSSE.ts` — Frontend SSE consumer (reuse directly)

### Frontend Patterns
- `src/frontend/src/types/itinerary.ts` — ChatMessage interface (already exists)
- `src/frontend/src/views/HomeView.vue` — chat-input-bar pattern for reference
- `src/frontend/src/App.vue` — Where floating bubble should be registered

### Database
- `src/backend/models/database.py` — Existing model patterns (add chat_messages here)
- `alembic/` — Migration for new table

### Prior Phase Context
- `.planning/phases/13-memory-skills/13-CONTEXT.md` — Memory tools (read_memories, write_memory) that work in chat
- `.planning/phases/14-pipeline-integration/14-CONTEXT.md` — Agent SSE patterns established

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useSSE` composable: directly reusable for chat SSE consumption
- `ChatMessage` type: already defined in `types/itinerary.ts`
- `PipelineSSEHooks`: can be instantiated in chat route for tool progress events
- `EventBus`: subscribe/emit/done pattern works for chat SSE
- `build_agent_instructions()`: skill matching works for chat messages
- `get_sdk_agent()`: cached Agent with 12 tools, just needs instruction override

### Established Patterns
- SSE route pattern: `StreamingResponse(event_stream(), media_type="text/event-stream")` with queue-based EventBus
- AgentContext construction: inline in route handler (like generate.py:46-54)
- Tool error handling: Chinese error messages returned to LLM
- Auth gating: `get_current_user_optional` returns None for anonymous

### Integration Points
- `App.vue`: Register floating chat bubble component
- `src/backend/api/routes/`: New `chat.py` route file
- `src/backend/main.py`: Register chat router
- `src/backend/models/database.py`: Add ChatMessage model
- `alembic/`: New migration for chat_messages table

</code_context>

<specifics>
## Specific Ideas

- User explicitly said: "没有会话历史数据，重要信息应该已经临时化记录存储" — no session history UI, memory tools handle important data persistence
- Floating bubble should feel like a travel-savvy friend is always available to help
- Anonymous users get a taste of the agent but must login for memory/personalization

</specifics>

<deferred>
## Deferred Ideas

- Chat history list / session management UI — not needed, memory handles persistence
- Image/file attachments in chat — future enhancement
- Chat in adjust pipeline — adjust uses its own flow
- Multi-agent conversations — future consideration
- Session cleanup job — no expiry needed per user decision

</deferred>

---

*Phase: 15-chat-integration*
*Context gathered: 2026-04-21*
