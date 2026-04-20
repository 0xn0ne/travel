# Roadmap: 拾途 (Shí Tú)

## Overview

Taste-based travel itinerary generator for 18-35 year old Chinese travelers. The product uses curated taste data + SOUL prompt to generate warm, personalized single-city itineraries with a "local friend" voice.

## Milestones

- ✅ **v1.0 MVP** — Phases 0-4 + E2E (shipped 2026-04-16) — [Archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Pipeline Quality + UI Redesign** — Phases 6-10 (in progress)
- 📋 **v1.2 AI Agent Tool System** — Phases 11-15 (planned)

## Phases

**Phase Numbering:**
- Integer phases (6, 7, 8): Planned milestone work
- Decimal phases (6.1, 6.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

### ✅ v1.0 MVP (Phases 0-4 + E2E) — SHIPPED 2026-04-16

<details>
<summary>v1.0 phase summary</summary>

- [x] Phase 0: SOUL Validation (7/7 plans) — completed 2026-04-16
- [x] Phase 1: Foundation & Data Pipeline (4/4 plans) — completed 2026-04-16
- [x] Phase 2: Core Generation + SSE (4/4 plans) — completed 2026-04-16
- [x] Phase 3: Adjust & Feedback (3/3 plans) — completed 2026-04-16
- [x] Phase 4: Polish (2/2 plans) — completed 2026-04-16
- [x] E2E Integration (UAT 21/22 passed) — completed 2026-04-16

**Key accomplishments:**
1. SOUL Prompt + Taste Data 4-stage pipeline
2. SSE real-time streaming architecture
3. Interactive adjustment with preview confirmation
4. Blind test A/B/C infrastructure
5. Docker deployment with nginx SSE support

**See:** [v1.0 archive](milestones/v1.0-ROADMAP.md) for full details

</details>

### 🚧 v1.1 Pipeline Quality + UI Redesign (In Progress)

**Milestone Goal:** Fix core pipeline to use real Amap POI search, redesign frontend for excitement and content richness, complete auth flow, add second city, and fix critical technical debt.

- [x] **Phase 6: Infrastructure & Pipeline Fixes** — Fix foundations: migrations, caching, test runner, production guards — **completed 2026-04-16**
- [x] **Phase 7: Data Expansion & City Support** — Expand pipeline: second city, dynamic POI search, auto-seeding, user preferences — **completed 2026-04-17**
- [x] **Phase 8: Auth & User System** — Complete auth: backend fix, frontend login/register, settings, itinerary history — **completed 2026-04-17**
- [ ] **Phase 9: UI Redesign & Rich Display** — Visual overhaul: warm palette, rich POI cards, journey loading, exciting home
- [ ] **Phase 10: Map & Sharing** — Map visualization with Amap JS + itinerary sharing via link

### 📋 v1.2 AI Agent Tool System (Planned)

**Milestone Goal:** Add model-agnostic AI Agent tool calling system — agent autonomously calls business tools during itinerary generation and user conversations, with memory, skills, and real-time streaming progress.

- [x] **Phase 11: Agent Framework Core** — Tool-call loop, registry, iteration guard + error recovery
- [ ] **Phase 12: Business & General Tools** — POI search, weather, preferences, web search, file I/O, command (reserved)
- [ ] **Phase 13: Memory & Skills** — Per-user SQLite memory, skill auto-activation, pre-built skill packs
- [ ] **Phase 14: Pipeline Integration** — New Agent Stage in existing pipeline, SSE tool-call progress
- [ ] **Phase 15: Chat Integration** — Chat API, streaming responses, frontend chat UI

## Phase Details

### Phase 6: Infrastructure & Pipeline Fixes
**Goal**: Technical foundations are solid — migrations work, caching is enabled, tests pass, production is guarded
**Depends on**: v1.0 (Phases 0-4)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, PIPE-02, PIPE-04
**Success Criteria** (what must be TRUE):
  1. `alembic upgrade head` runs cleanly and creates all current tables from scratch
  2. Backend refuses to start in production environment without `JWT_SECRET_KEY` configured
  3. `seed_pois.py` runs without errors and correctly populates POI latitude/longitude fields
  4. AmapCache caches POI search results — repeat identical queries return cached data without hitting Amap API
  5. Test runner endpoint `/test-runner/generate` produces A/B/C itineraries for all configured scenarios
**Plans**: 2 plans

Plans:
- [x] 06-01-PLAN.md — Alembic migrations + JWT production guard + auto-seed (INFRA-01, INFRA-02, INFRA-03)
- [x] 06-02-PLAN.md — AmapService cache injection + Test Runner fix (PIPE-02, PIPE-04)

### Phase 7: Data Expansion & City Support
**Goal**: Pipeline supports multiple cities with dynamic POI expansion and personalized user preferences
**Depends on**: Phase 6
**Requirements**: CITY-01, CITY-02, CITY-03, CITY-04, PIPE-01, PIPE-03
**Success Criteria** (what must be TRUE):
  1. Second city (Hangzhou or Chengdu) has curated Tier A POIs and auto-tiered Tier B/C data available in the database
  2. Pipeline generates a complete itinerary for the second city using city config — no hardcoded "上海" references in pipeline logic
  3. Fresh Docker deploy auto-seeds the database with POIs and test scenarios — no manual script execution needed
  4. Stage 2 dynamically expands POI candidates via Amap `search_pois()`, merging results with curated DB data and deduplicating by amap_id
  5. User's `taste_tags_default` and `budget_default` from their profile are read and passed into the generation pipeline
**Plans**: 3 plans

Plans:
- [x] 07-01-PLAN.md — City config system + pipeline integration (CITY-02)
- [x] 07-02-PLAN.md — Hangzhou POI data + multi-city auto-seeding (CITY-01, CITY-03, CITY-04)
- [x] 07-03-PLAN.md — Dynamic Amap POI expansion + user preferences pipeline (PIPE-01, PIPE-03)

### Phase 8: Auth & User System
**Goal**: Users can create accounts, manage taste preferences, and browse their itinerary history
**Depends on**: Phase 6
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05
**Success Criteria** (what must be TRUE):
  1. User can register with email/password, log in to receive a JWT, and the `/me` endpoint returns their profile
  2. Frontend displays login/register modal, stores JWT in localStorage, and auto-attaches it to all API requests
  3. Protected pages (itinerary list, settings) redirect unauthenticated users to the login modal
  4. User can view and edit their taste tags (tag selector) and budget preference (radio buttons) on a settings page, saved via PUT `/auth/profile`
  5. User can view a list of their past itineraries as cards showing title, city, and date — clicking navigates to the full itinerary view
**Plans**: 2 plans
**UI hint**: yes

Plans:
- [x] 08-01-PLAN.md — Backend auth verification + profile/itinerary API (AUTH-01, AUTH-04, AUTH-05)
- [x] 08-02-PLAN.md — Frontend auth modal, route guards, settings, itinerary list (AUTH-02, AUTH-03, AUTH-04, AUTH-05)

### Phase 9: UI Redesign & Rich Display
**Goal**: The app feels exciting and warm — rich POI information is beautifully displayed with a "旅途中" atmosphere
**Depends on**: Phase 7, Phase 8
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. App uses a bright warm color palette (sand/coral/ocean tones) with card-based layout featuring depth and warmth — not a generic tech-blue interface
  2. POI detail cards display highlight_note (推荐理由), vibe_description (氛围描述), tier badge (★/○/·), walk_to_next_minutes, and opening hours
  3. Each POI shows data source attribution badge: "人工精选" for Tier A, "高德地图" for Amap-sourced, "AI推荐" for LLM-suggested
  4. Generation progress shows journey-themed animation with travel-imagery stage messages — not sterile progress bars
  5. Home page hero area creates emotional pull with example prompts presented as clickable journey cards — not plain text tags
**Plans**: 5 plans
**UI hint**: yes

Plans:
- [x] 09-01-PLAN.md — Warm design system foundation: CSS custom properties + NConfigProvider theme-overrides (UI-01)
- [x] 09-02-PLAN.md — POI card rich display: tier badges, data source SVG icons, expanded detail (UI-02, UI-03)
- [x] 09-03-PLAN.md — Hero gradient + journey cards + warm progress bar with travel messages (UI-04, UI-05)
- [x] 09-04-PLAN.md — Global warm color migration: header, day section, timeline, list, feedback (UI-01)
- [x] 09-05-PLAN.md — ItineraryView warm color migration + final visual verification checkpoint (UI-01)

### Phase 10: Map & Sharing
**Goal**: Itineraries come alive on an interactive map and are shareable with a single link
**Depends on**: Phase 9
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04, SHARE-01, SHARE-02
**Success Criteria** (what must be TRUE):
  1. Amap JS map displays POI markers with tier-colored pins (gold/silver/bronze) and walking route lines between consecutive POIs
  2. Clicking a POI in the timeline highlights and pans to the corresponding map marker; clicking a map marker expands the timeline POI card
  3. Each day's route is color-coded on the map (Day 1 blue, Day 2 green, Day 3 orange) with auto-zoom to fit the selected day's POIs
  4. Map layout is responsive — split view (map + timeline side-by-side) on desktop, tabbed/stacked layout on mobile
  5. User can copy a share link from itinerary view header; the shared page has correct `og:title` and `og:description` meta tags for social previews
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [ ] 10-01-PLAN.md — Backend API enrichment: coordinates, meta, config endpoint + CSS day colors (MAP-01, MAP-03, SHARE-01)
- [ ] 10-02-PLAN.md — MapView component, responsive layout, bidirectional sync, ShareButton, OG tags (MAP-01, MAP-02, MAP-03, MAP-04, SHARE-01, SHARE-02)
- [ ] 10-03-PLAN.md — Visual verification checkpoint (MAP-01, MAP-02, MAP-03, MAP-04, SHARE-01, SHARE-02)

### 📋 v1.2 AI Agent Tool System

### Phase 11: Agent Framework Core
**Goal**: AI agent can reason about tasks and call registered tools to accomplish them — the foundation everything else depends on
**Depends on**: Phase 10 (v1.1 complete)
**Requirements**: AGENT-01, AGENT-02, AGENT-04
**Success Criteria** (what must be TRUE):
  1. Given a registered tool, the agent loop receives a user message, LLM decides to call the tool, executes the function, and returns the result to the LLM for further reasoning
  2. Tools register dynamically with name, description, and Pydantic input schema — the registry validates schemas and exposes them as OpenAI function-calling format
  3. After 8 tool-call rounds in a single message, the agent stops and returns a graceful message instead of looping infinitely
  4. When a tool execution raises an error, the error is caught and returned as error context to the LLM, which can attempt recovery with a different tool or arguments
**Plans**: 2 plans

Plans:
- [x] 11-01-PLAN.md — LLMClient + ToolResult + ToolRegistry + config.yml (AGENT-02)
- [x] 11-02-PLAN.md — AgentLoop with tool-call cycle, iteration guard, error recovery, SSE, DI (AGENT-01, AGENT-04)

### Phase 12: Business & General Tools
**Goal**: Agent has a complete toolkit to help travelers — search POIs, check weather, read preferences, search the web, and manage files
**Depends on**: Phase 11
**Requirements**: BIZ-01, BIZ-02, BIZ-03, BIZ-04, TOOL-01, TOOL-02, TOOL-03, TOOL-04
**Success Criteria** (what must be TRUE):
  1. Agent searches POI database by city + keyword and returns name, rating, tier, coordinates, and highlight_note
  2. Agent queries weather forecast for a city and date range, returning temperature, conditions, and travel suggestions
  3. Agent reads current user's taste tags, budget preference, and past itinerary history from the database
  4. Agent searches the web by keywords as a fallback when POI DB results are insufficient, returning top results with title + snippet + URL
  5. Agent reads and writes files within a designated `data/agent_memory/` directory, but cannot access paths outside that directory
**Plans**: TBD

### Phase 13: Memory & Skills
**Goal**: Agent remembers user preferences across conversations and activates the right skill combinations automatically
**Depends on**: Phase 12
**Requirements**: MEM-01, MEM-02, MEM-03, SKILL-01, SKILL-02, SKILL-03
**Success Criteria** (what must be TRUE):
  1. New `agent_memories` table stores structured entries with user_id, key, value (JSON), and timestamps — agent writes memories during conversation and reads them at session start
  2. Agent only accesses memories of the authenticated user; unauthenticated sessions have no persistent memory
  3. Pre-built skills ("行程规划", "美食探索", "本地人推荐") define named tool subsets with context prompts, each loaded from a JSON config file in `data/skills/`
  4. When a user message matches a skill's trigger conditions (keywords, city, topic), the skill auto-activates: its tools are enabled and context prompt is injected into the system message
**Plans**: TBD

### Phase 14: Pipeline Integration
**Goal**: Agent enriches itinerary generation by using tools to gather real-time data, with visible progress streamed to the user
**Depends on**: Phase 11, Phase 12
**Requirements**: PIPE-01, PIPE-02, AGENT-03
**Success Criteria** (what must be TRUE):
  1. A new Agent Stage runs between Stage 2 (pre-filter) and Stage 3 (LLM+SOUL) — the agent receives filtered POI candidates + user intent, uses tools to enrich data, and passes enriched context to Stage 3
  2. During agent tool calls in the pipeline, SSE events stream progress messages like "正在搜索附近好去处..." through the existing EventBus — the user sees meaningful progress, not silent waiting
  3. Tool-call mechanics (JSON schemas, function names, raw arguments) never appear in the user-facing SSE stream — only human-readable progress messages and final results
**Plans**: TBD

### Phase 15: Chat Integration
**Goal**: Users can have a real-time conversation with the AI assistant that transparently uses tools to answer their questions
**Depends on**: Phase 13, Phase 14
**Requirements**: CHAT-01, CHAT-02, CHAT-03
**Success Criteria** (what must be TRUE):
  1. `POST /api/chat` accepts a user message + optional session_id, processes it through the agent loop with tool calling, and returns a streaming SSE response with the final text answer
  2. A floating chat bubble or side panel in the itinerary view lets users type messages and see streaming AI responses — tool calls are transparent, user only sees final answer
  3. Messages are stored in `chat_messages` table per session; the agent receives the last N messages as context when responding to a new message
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 0. SOUL Validation | v1.0 | 7/7 | Complete | 2026-04-16 |
| 1. Foundation | v1.0 | 4/4 | Complete | 2026-04-16 |
| 2. Core Generation | v1.0 | 4/4 | Complete | 2026-04-16 |
| 3. Adjust & Feedback | v1.0 | 3/3 | Complete | 2026-04-16 |
| 4. Polish | v1.0 | 2/2 | Complete | 2026-04-16 |
| 6. Infrastructure & Pipeline Fixes | v1.1 | 2/2 | Complete | 2026-04-16 |
| 7. Data Expansion & City Support | v1.1 | 3/3 | Complete | 2026-04-17 |
| 8. Auth & User System | v1.1 | 2/2 | Complete | 2026-04-17 |
| 9. UI Redesign & Rich Display | v1.1 | 5/5 | Complete | 2026-04-17 |
| 10. Map & Sharing | v1.1 | 0/3 | Not started | - |
| 11. Agent Framework Core | v1.2 | 1/2 | In Progress | - |
| 12. Business & General Tools | v1.2 | 0/? | Not started | - |
| 13. Memory & Skills | v1.2 | 0/? | Not started | - |
| 14. Pipeline Integration | v1.2 | 0/? | Not started | - |
| 15. Chat Integration | v1.2 | 0/? | Not started | - |

---
*Roadmap created: 2026-04-15*
*Last updated: 2026-04-20 — v1.2 roadmap created (Phases 11-15, 23 requirements)*
