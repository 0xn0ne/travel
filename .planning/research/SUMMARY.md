# Project Research Summary

**Project:** 拾途 (Shí Tú) — Taste-based Travel Itinerary Generator
**Domain:** AI-powered travel itinerary generation (Chinese market)
**Researched:** 2026-04-15
**Confidence:** MEDIUM-HIGH

## Executive Summary

拾途 is an AI-powered travel itinerary generator that differentiates through **curated taste data** and a **warm "local friend" narrative voice (SOUL)** rather than competing on booking integration or route optimization like major Chinese OTAs (携程, 飞猪). The product uses a 4-stage generation pipeline: intent extraction → POI pre-filtering → LLM+SOUL generation → route validation, delivered via a Vue 3 SPA frontend streaming results through Server-Sent Events.

The recommended stack is Python 3.12+ / FastAPI 0.135.3 / Vue 3 / SQLite (MVP) / DeepSeek-V3 via OpenAI-compatible API. This stack was chosen for async-first architecture (critical for LLM streaming), mature Chinese-market UI support (Naive UI), and zero-config deployment (SQLite on single VPS). The core risk is that the SOUL narrative voice and taste curation are the actual product moat — if Phase 0 blind tests don't validate ≥60% preference, the entire approach needs rethinking before any engineering investment.

Key risks identified: (1) LLM fabricating non-existent venues is the highest-severity failure mode, prevented by strict POI-ID-based generation; (2) Amap API rate limits (5,000 calls/month free tier) require aggressive caching before launch; (3) SSE timeout/config must support 30-60s generation windows; (4) feedback loop must be designed into the data model from day one or becomes cosmetic decoration.

## Key Findings

### Recommended Stack

**Python 3.12+ / FastAPI 0.135.3** — FastAPI's built-in SSE support (since 0.135.0) eliminates `sse-starlette` dependency. Async-native design critical for LLM streaming pipeline. Vue 3 + Naive UI + Tailwind CSS 4 chosen for Chinese-market UI readiness (Naive UI has Chinese-first docs, tree-shaking, no jQuery). SQLite (MVP) with SQLAlchemy 2.0 async + aiosqlite; PostgreSQL migration path is clean via dialect abstraction. DeepSeek-V3 accessed via official `openai` SDK with `base_url='https://api.deepseek.com'` — NOT a custom HTTP client.

**Core technologies:**
- **FastAPI 0.135.3:** SSE streaming, async/await, Pydantic v2 integration — the async backbone
- **Vue 3.5.32 + Naive UI 2.44.1:** Chinese-market-ready component library with modern API
- **SQLAlchemy 2.0.49 + aiosqlite:** Async ORM with typed `Mapped[]` syntax, non-blocking I/O
- **DeepSeek-V3 (`deepseek-chat`):** 128K context, OpenAI-compatible API, cost-effective for Chinese generation
- **uvicorn 0.44.0:** ASGI server with `--workers` for production
- **Pydantic 2.13.1 + pydantic-settings:** Typed config management replacing python-dotenv
- **tenacity 9.1.4:** Retry logic with exponential backoff for LLM/API calls
- **Tailwind CSS 4.2.2:** CSS-first config, works with Naive UI for custom styling

**What NOT to use:** `sse-starlette` (redundant with FastAPI 0.135+), Flask/Django (inferior async), `requests` (sync only, blocks event loop), Vuex (deprecated), `python-dotenv` (redundant with pydantic-settings), Celery/Redis (overkill for MVP), MongoDB (relational data), GraphQL (unnecessary complexity).

### Expected Features

**Must have (table stakes):**
- Natural language input → structured intent extraction — conversational entry point
- Day-by-day itinerary output with time-sequenced POI nodes
- POI data with basic info (name, photo, rating, hours) from Amap API
- Route/time validation via Amap Walking API — impossible routes destroy trust
- Budget awareness and interest/style preference filtering
- Edit/adjust via dialog after generation — no first draft is perfect
- Mobile-responsive web (target demographic 18-35 is mobile-first)
- Save/load itineraries with simple JWT auth
- Chinese language UI — all copy in Simplified Chinese

**Should have (competitive differentiators):**
- **SOUL narrative voice** — warm, opinionated "本地朋友" tone vs. encyclopedia summaries. THE differentiator.
- **3-tier curated POI database** — Tier A (hand-picked, 10-15/city) gets rich narrative; Tier B (LLM-labeled); Tier C (raw Amap)
- **Taste-tag scoring (D1/D3/D7)** — quantified taste profile per POI for preference matching beyond category filters
- **Emotional pacing** — rhythm-aware itineraries (quiet morning → energetic afternoon → cozy evening)
- **SSE streaming with 4-stage progress** — "正在理解你的需求 → 正在挑选好地方 → 正在规划行程 → 正在优化路线"
- **Highlight notes per POI** — "为什么推荐这个?" answered in friend-voice, not Wikipedia voice

**Defer (v2+):**
- WeChat Mini Program — validate on web first
- Multi-city/cross-city trips — breaks single-city depth positioning
- Social sharing (朋友圈/小红书) — shifts brand from "personal friend" to "performative content"
- Booking integration — transforms into OTA platform, kills the "local friend" vibe
- UGC/reviews — content moderation nightmare, dilutes Tier A quality
- Fine-tuned LLM model — SOUL prompts + taste data = controllable quality without training cost

### Architecture Approach

The system uses a **4-stage pipeline architecture** with SSE streaming for real-time progress feedback. Stage 1 (Intent Extraction LLM, ~500 tokens) parses natural language into structured intent. Stage 2 (Data Pre-filter, pure Python async) queries SQLite POI database and filters by destination, tier balance, and user constraints. Stage 3 (Itinerary Generation LLM + SOUL, ~12K tokens) creates day-by-day itinerary using concrete POI IDs supplied by Stage 2. Stage 4 (Validation Layer) calls Amap Walking API O(N) between consecutive nodes to verify route feasibility.

**Major components:**
1. **Vue Frontend SPA** — Chat UI, SSE event handling via `useSSE.ts` composable, itinerary timeline visualization
2. **FastAPI SSE Router** — Manages streaming responses, stage progress events, connection lifecycle
3. **4-Stage Pipeline Coordinator** — Orchestrates stage execution, emits events, handles failures/retry
4. **LLM Gateway** — DeepSeek-V3 client via `openai` SDK, retry/logging abstraction
5. **POI Database** — SQLite with FTS5 for search, 3-tier POI data model
6. **Pydantic Validation Layer** — IntentOutput, POICandidate, Itinerary, ValidationResult models

### Critical Pitfalls

1. **LLM Fabricates Venues** — DeepSeek-V3 hallucinates specific venue names/addresses when not constrained. Prevent by: never letting LLM generate free-text venue names; Stage 2 supplies concrete POI records; Stage 3 only selects from POI IDs; implement hallucination check verifying all referenced POI IDs exist in SQLite.

2. **Amap Rate Limits** — Free tier is 5,000 calls/month TOTAL, not per day. Full route validation (Stage 4) can consume 15-30+ calls per itinerary. Prevent by: aggressive POI caching at data layer; per-user call budgets; batch route validation; set alert at 80% of monthly quota.

3. **"Taste Mode" Produces Generic Results** — SOUL prompt generates warm tone but recommendations are same 标准景点 everyone suggests. Prevent by: enforce ≥40% Tier A POI inclusion per itinerary; make taste_tags granular (not just "文艺" but "独立书店|复古唱片店"); track POI repetition rate; Phase 0 must test recommendation quality separately from writing quality.

4. **SSE Stream Drops Mid-Generation** — 30-60s generation exceeds default proxy timeouts; frontend left in limbo. Prevent by: set SSE timeout to 120s minimum; send ping/pong events every 15s; implement client-side reconnection with exponential backoff; always emit terminal `[DONE]` event.

5. **Feedback Loop Produces No Actionable Iterations** — "不准" button captures votes but data never feeds back into taste system. Prevent by: design feedback data model capturing *why* (not just vote); build weekly digest for low-rated POIs; define update threshold (e.g., >30% "不准" → demote to Tier C); close the loop with users.

## Implications for Roadmap

Based on research, the recommended phase structure prioritizes validation before investment and builds dependencies from data layer up.

### Phase 0: SOUL Prompt Validation (BLOCKING)
**Rationale:** This is the core product hypothesis. If SOUL + taste data doesn't produce ≥60% preference in blind tests vs. competitors, engineering investment is wasted.
**Delivers:** Validated SOUL prompt + taste data approach; separate tests for writing quality AND recommendation quality
**Avoids:** Pitfall #5 (generic taste results), Pitfall #9 (Phase 0 validates wrong thing)
**Research flag:** Needs user study design + blind test methodology — consider `/gsd-research-phase` for this

### Phase 1: Foundation + Data Pipeline
**Rationale:** Cannot build features without POI data; cannot validate routes without Amap integration; architecture must support async from day one.
**Delivers:** Project structure, SQLite schema with proper UTF-8 encoding, LLM client wrapper, Amap POI pipeline (1-2 cities), Stage 1 + Stage 2 working end-to-end
**Stack:** Python 3.12, FastAPI 0.135.3, SQLAlchemy 2.0 async, aiosqlite, DeepSeek-V3 via openai SDK
**Avoids:** Pitfall #3 (Amap rate limits) — implement caching before any user-facing launch; Pitfall #6 (Chinese encoding); Pitfall #4 (route validation) — add multi-mode comparison
**Research flag:** Standard FastAPI patterns — can proceed without additional research

### Phase 2: Core Generation + SSE
**Rationale:** Stage 3 is the most complex (12K token generation with SOUL); needs iteration on prompt engineering; SSE frontend integration is well-documented.
**Delivers:** Stage 3 (Itinerary Generation with SOUL narrative), Stage 4 (Route Validation), SSE streaming to frontend, Vue timeline visualization
**Stack:** FastAPI SSE (EventSourceResponse), Vue 3 + Naive UI, Pinia store
**Implements:** 4-stage pipeline coordinator, Pydantic output parsing for LLM responses
**Avoids:** Pitfall #1 (LLM fabrication) — enforce POI-ID-based generation; Pitfall #7 (SSE drops) — configure timeouts and ping events
**Research flag:** Standard SSE patterns — can proceed without additional research

### Phase 3: Edit/Adjust + Feedback
**Rationale:** Users need to refine generated itineraries; feedback mechanism is the data flywheel foundation.
**Delivers:** Adjustment flow (preview → confirm), feedback collection ("准不准?"), feedback analytics pipeline
**Implements:** Request-response with confirmation pattern; feedback data model with dimension capture
**Avoids:** Pitfall #8 (unused feedback loop) — design data model before launch
**Research flag:** Standard UX patterns — can proceed without additional research

### Phase 4: Polish + Edge Cases
**Rationale:** Production hardening based on real usage patterns.
**Delivers:** Error handling + retry logic, response caching, performance optimization, edge case handling
**Addresses:** Recovery strategies from PITFALLS.md; TTL enforcement for POI data freshness
**Research flag:** May need research on scaling patterns if concurrent user targets exceed 100

### Phase Ordering Rationale

- **Phase 0 before all engineering** — validates core hypothesis before investment
- **Foundation before features** — data pipeline is prerequisite for all POI-dependent features
- **SSE after single-stage works** — debugging pipeline + SSE simultaneously is higher risk
- **Feedback in Phase 3** — must have completed itineraries before users can meaningfully adjust/evaluate them
- **Polish last** — address edge cases after core loop is validated with real users

## Research Flags

**Needs deeper research during planning:**
- **Phase 0 (Blind Test Design):** Methodology for separating writing quality from recommendation quality — may need user research expertise or external validation
- **Phase 1 (Amap API quota strategy):** Exact rate limit behavior under load; whether paid tier is cost-effective at what user scale
- **Phase 4 (Scaling beyond 100 users):** Redis pub/sub for SSE if multi-worker deployment; exact caching strategy for POI data

**Standard patterns (skip research-phase):**
- **Phase 1 (Backend foundation):** FastAPI + SQLAlchemy async patterns are well-documented
- **Phase 2 (SSE integration):** FastAPI EventSourceResponse documented; Vue SSE composable is standard pattern
- **Phase 3 (Edit/adjust):** Preview → confirm UX pattern is common; no novel integration

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All version pins verified against PyPI/npm registries; DeepSeek OpenAI-compatible API confirmed via official docs; FastAPI 0.135.0 built-in SSE verified |
| Features | MEDIUM | Western competitors (Wanderlog, Layla.ai) verified via official sites; Chinese competitors (携程, 飞猪, 马蜂窝) based on training knowledge with limited web verification due to access restrictions |
| Architecture | MEDIUM | 4-stage pipeline pattern is standard; SSE implementation uses FastAPI documented APIs; Pydantic output parsing is well-established; scaling projections (0-10K users) are reasonable estimates |
| Pitfalls | MEDIUM | Domain knowledge + documented API behavior (Amap) is solid; LLM hallucination patterns are well-known; Chinese market user behavior based on general knowledge rather than specific post-mortems |

**Overall confidence:** MEDIUM-HIGH

The stack recommendations are highly confident (verified sources). The feature set is reasonably confident (competitive analysis partially limited by Chinese market access). The architecture is sound but the specific scaling thresholds (when to add Redis, when to migrate to PostgreSQL) will need validation. Pitfalls are identified from general patterns but some (feedback loop effectiveness, Phase 0 test design) will only be validated through actual user testing.

### Gaps to Address

- **Chinese competitor deep-dive:** 携程AI, 飞猪AI, 马蜂窝 features/limitations could not be fully verified — recommend discrete research sprint before Phase 0 to ensure competitive positioning is accurate
- **Phase 0 blind test methodology:** Designing a test that separates SOUL writing quality from recommendation quality requires expertise in user research methodology — may need external consultation
- **Amap API behavior under load:** Exact rate limit enforcement, error handling, and optimal caching strategy needs load testing to validate
- **User taste profile data compliance:** PIPL compliance for storing user preference data needs legal review before any user data is collected

## Sources

### Primary (HIGH confidence)
- [FastAPI GitHub releases](https://github.com/tiangolo/fastapi/releases) — verified 0.135.3, built-in SSE in 0.135.0
- [Vue 3 GitHub releases](https://github.com/vuejs/core/releases) — verified 3.5.32
- [SQLAlchemy GitHub releases](https://github.com/sqlalchemy/sqlalchemy/releases) — verified 2.0.49
- [DeepSeek API Documentation](https://api.deepseek.com/) — OpenAI-compatible format, model aliases, base_url
- [Amap Web Service API Documentation](https://lbs.amap.com/api/webservice/summary/) — POI fields, rate limits, geocoding behavior
- [Pydantic GitHub releases](https://github.com/pydantic/pydantic/releases) — verified 2.13.1
- [Naive UI npm registry](https://www.npmjs.com/package/naive-ui) — verified 2.44.1
- [Wanderlog Official Site](https://wanderlog.com) — verified feature set
- [Layla.ai Official Site](https://layla.ai) — verified feature set

### Secondary (MEDIUM confidence)
- [PROJECT.md](./PROJECT.md) — technology constraints and 3-tier POI architecture confirmed
- [穷游 (Qyer) Official Site](https://www.qyer.com) — verified feature set
- [TripIt Official Site](https://www.tripit.com) — verified feature set
- Amap API behavior — verified via official docs; actual rate limit enforcement under load unverified
- Chinese competitor analysis (携程, 飞猪, 马蜂窝) — training knowledge + partial web verification

### Tertiary (LOW confidence)
- Chinese market user behavior patterns — general knowledge, needs validation during Phase 0 user research
- Feedback loop effectiveness projections — no comparable product data available
- Scaling projections (when exactly to add Redis, migrate to PostgreSQL) — estimates based on general patterns

---
*Research completed: 2026-04-15*
*Ready for roadmap: yes*
