# Stack Research

**Domain:** Taste-based travel itinerary generator (品味行程生成器)
**Researched:** 2026-04-15
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.12+ | Backend runtime | Performance improvements over 3.11, async/await mature, wide library ecosystem. 3.13 too new for production stability. |
| **FastAPI** | 0.135.3 | Backend framework | **Built-in SSE support since 0.135.0** — eliminates need for sse-starlette. Streaming JSON Lines since 0.134.0. Pydantic v2 integration, async-native, OpenAPI auto-docs. Perfect for LLM streaming pipeline. |
| **Vue 3** | 3.5.32 | Frontend framework | Composition API stable, `<script setup>` syntax, excellent reactivity system. Pre-selected by project. Vue 3.6 still in beta, avoid. |
| **SQLAlchemy** | 2.0.49 | ORM + database layer | Mature async support via `create_async_engine`. Type-annotated `Mapped[]` syntax. Essential for the 3-tier POI data model. |
| **SQLite** | (system) | Primary database (MVP) | Zero-config, single-file, no server. Perfect for single-VPS deployment. WAL mode for concurrent reads. Upgrade path to PostgreSQL is clean via SQLAlchemy abstraction. |
| **DeepSeek-V3** | `deepseek-chat` | LLM engine | Accessed via OpenAI-compatible API using `openai` SDK with `base_url='https://api.deepseek.com'`. Model alias `deepseek-chat` = DeepSeek-V3.2 with 128K context window. Cost-effective for Chinese-language generation. |

### Supporting Libraries — Backend

| Library | Version | Purpose | Why This One |
|---------|---------|---------|--------------|
| **uvicorn** | 0.44.0 | ASGI server | Standard FastAPI server. WebSocket keepalive pings, HTTP/1.1 pipelining. Active development. Use `--workers` for production. |
| **Pydantic** | 2.13.1 | Data validation | Ships with FastAPI but pin explicitly. v2.13 has polymorphic serialization, performance gains. Used for request/response models, POI schemas, LLM output validation. |
| **pydantic-settings** | 2.13.1 | Configuration management | Env-var loading, `.env` file support, nested settings. Use for API keys (DeepSeek, 高德), database URLs, feature flags. Replaces python-dotenv. |
| **openai** | 2.31.0 | DeepSeek API client | **Use this, NOT a custom HTTP client.** DeepSeek exposes OpenAI-compatible API. Set `base_url='https://api.deepseek.com'`. Built-in streaming, retry, type-safe responses. |
| **SQLAlchemy[asyncio]** | 2.0.49 | Async DB operations | Adds `greenlet` dependency for async session support. Use `AsyncSession` with `aiosqlite` driver. |
| **aiosqlite** | 0.22.1 | Async SQLite driver | Bridges sqlite3 to asyncio. Required because SQLAlchemy async engine needs an async driver. |
| **alembic** | 1.18.4 | Database migrations | Standard for SQLAlchemy. Use for schema evolution as POI model matures through phases. |
| **httpx** | 0.28.1 | HTTP client (external APIs) | Async-capable, HTTP/2 support. For calling 高德 POI search, weather APIs, any external data sources. Not for DeepSeek (use `openai` SDK instead). |
| **tenacity** | 9.1.4 | Retry logic | Wrap LLM calls with exponential backoff. DeepSeek API can rate-limit or timeout. Configurable stop conditions, retry on specific exceptions. |
| **httpx-sse** | 0.4.3 | SSE client for httpx | For consuming external SSE endpoints if any third-party APIs use SSE. Not needed for our own SSE (FastAPI handles that). |

### Supporting Libraries — Frontend

| Library | Version | Purpose | Why This One |
|---------|---------|---------|--------------|
| **Vite** | 8.0.8 | Build tool / dev server | Fast HMR, native ESM. Standard for Vue projects. `create-vite@9.0.4` for scaffolding. |
| **@vitejs/plugin-vue** | 6.0.6 | Vue SFC support in Vite | Official plugin. Compatible with Vite 5/6/7/8. Required for `.vue` files. |
| **vue-router** | 5.0.4 | Client-side routing | Official Vue router. Use for page navigation (home → itinerary view → settings). |
| **Pinia** | 3.0.4 | State management | Official Vue store. Replaces Vuex. Composition API-friendly. Pinia 3.0 is ESM-only, dropped Vue 2 support. |
| **Naive UI** | 2.44.1 | Component library | **Critical choice for Chinese-market app.** Tree-shakeable, TypeScript-native, Chinese-first documentation. Components: calendar, cards, skeleton loading, drawer — all needed for itinerary display. No jQuery dependencies. |
| **Tailwind CSS** | 4.2.2 | Utility CSS framework | v4 uses CSS-first config (no `tailwind.config.js`). Works with Naive UI for custom styling on top of component defaults. Use for layout, spacing, custom itinerary card styles. |
| **axios** | 1.15.0 | HTTP client | For REST API calls (non-SSE). Request/response interceptors, timeout config, error handling. |
| **@vueuse/core** | 14.2.1 | Vue composition utilities | `useFetch`, `useStorage`, `useDebounce`, `useIntersectionObserver`. Reduces boilerplate for common patterns. |
| **@amap/amap-jsapi-loader** | 1.0.1 | 高德地图 loader | Official Amap JS API loader. Lazy-loads map SDK. For POI display on map, route visualization. |

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| **ruff** | 0.15.10 | Python linter + formatter | Replaces flake8, black, isort. Single tool, ~100x faster than flake8. Configure `pyproject.toml`. |
| **pytest** | 9.0.3 | Python testing | Standard. Use with `pytest-asyncio` for async tests. |
| **pytest-asyncio** | 1.3.0 | Async test support | `async def test_` functions. Configure `asyncio_mode = "auto"` in `pyproject.toml`. |
| **TypeScript** | 5.x | Frontend type safety | Vue 3 + Vite have first-class TS support. Use `<script setup lang="ts">`. |
| **Docker Compose** | v2+ | Container orchestration | Single `docker-compose.yml` for backend + frontend + (optional) nginx. Single VPS deployment. |

## Installation

```bash
# === Backend (Python) ===
# Create project
mkdir backend && cd backend
python -m venv .venv && source .venv/bin/activate

# Core
pip install fastapi==0.135.3 uvicorn[standard]==0.44.0

# Database
pip install sqlalchemy[asyncio]==2.0.49 aiosqlite==0.22.1 alembic==1.18.4

# LLM & API
pip install openai==2.31.0 tenacity==9.1.4 httpx==0.28.1 httpx-sse==0.4.3

# Config & Validation
pip install pydantic==2.13.1 pydantic-settings==2.13.1

# Dev
pip install -D ruff==0.15.10 pytest==9.0.3 pytest-asyncio==1.3.0

# === Frontend (Vue) ===
# Scaffold with Vite
npm create vite@latest frontend -- --template vue-ts
cd frontend

# Core
npm install vue-router@5.0.4 pinia@3.0.4

# UI
npm install naive-ui@2.44.1
npm install -D tailwindcss@4.2.2 @tailwindcss/vite@4.2.2

# Utilities
npm install axios@1.15.0 @vueuse/core@14.2.1 @amap/amap-jsapi-loader@1.0.1
```

## Architecture Wiring

### SSE Streaming Pipeline

```
Vue Frontend                    FastAPI Backend                    DeepSeek API
    │                                │                                  │
    │  GET /api/itinerary/stream     │                                  │
    │  (EventSource / fetch)         │                                  │
    │───────────────────────────────>│                                  │
    │                                │  POST /chat/completions          │
    │                                │  (stream=true)                   │
    │                                │─────────────────────────────────>│
    │                                │                                  │
    │  SSE: data: {"stage":"prefilter"}                                 │
    │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│  SSE: data: {"delta":"..."}       │
    │                                │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
    │  SSE: data: {"stage":"gen",   │                                  │
    │         "content":"漫步在..."} │  Stream chunks forward           │
    │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
    │                                │                                  │
    │  SSE: data: [DONE]            │                                  │
    │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│                                  │
```

**Key**: FastAPI 0.135.0+ has built-in `StreamingResponse` with SSE support. No `sse-starlette` needed.

### DeepSeek Client Setup

```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
)

# Streaming call
stream = client.chat.completions.create(
    model="deepseek-chat",  # = DeepSeek-V3.2, 128K context
    messages=[...],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

### Frontend SSE Consumption

```typescript
// Use native EventSource for GET, or @microsoft/fetch-event-source for POST
const eventSource = new EventSource('/api/itinerary/stream?session_id=xxx')
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // Handle stage updates and content chunks
}
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not (For This Project) |
|----------|-------------|-------------|---------------------------|
| UI Library | **Naive UI** | Element Plus | Element Plus is heavier, more enterprise-focused. Naive UI has better tree-shaking, Chinese-first docs, more modern API design. |
| UI Library | **Naive UI** | Ant Design Vue | Ant Design Vue is great but carries Ant Design's design language which feels enterprise/corporate. Not ideal for a lifestyle/travel app targeting 18-35. |
| CSS | **Tailwind CSS 4** | UnoCSS | UnoCSS is faster but Tailwind has larger ecosystem, better Naive UI compatibility docs, and v4's CSS-first config closes the config-gap. |
| State | **Pinia 3** | Vuex 4 | Vuex is deprecated for Vue 3. Pinia is official replacement, simpler API, better TypeScript support. |
| LLM SDK | **openai** | httpx (custom) | openai SDK handles streaming protocol, retry, type safety, error parsing. Custom HTTP client would need to reimplement all of this. |
| DB Driver | **aiosqlite** | aiosqlite + sqlalchemy | aiosqlite IS the async driver. SQLAlchemy uses it via `create_async_engine("sqlite+aiosqlite:///...")`. No alternative needed. |
| HTTP Client | **httpx** | aiohttp | httpx has cleaner API, HTTP/2 support, better timeout handling. aiohttp is more verbose and less Pythonic. |
| Retries | **tenacity** | backoff | tenacity has more flexible retry strategies, better type hints, more active maintenance. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **sse-starlette** | FastAPI 0.135.0+ has built-in SSE support. This library is now redundant and adds unnecessary dependency. | FastAPI's `StreamingResponse` with `text/event-stream` media type |
| **Flask / Django** | Project requires async (LLM streaming, SSE, concurrent API calls). Flask/Django async stories are inferior to FastAPI. | FastAPI |
| **requests** | Synchronous only. Every external call blocks the event loop. Fatal for LLM streaming. | httpx (async) |
| **Vuex 4** | Deprecated for Vue 3. Boilerplate-heavy, poor TypeScript support. | Pinia 3 |
| **python-dotenv** | `pydantic-settings` handles `.env` files AND provides typed config with validation. Using both is redundant. | pydantic-settings |
| **Celery / Redis** | Overkill for MVP on single VPS. LLM calls are streaming (not background tasks). If async jobs needed later, use `asyncio.create_task` or lightweight task queue. | asyncio tasks for MVP; add task queue if needed later |
| **MongoDB** | Data is relational (POIs have categories, cities, ratings). SQL is the right fit. SQLite → PostgreSQL migration path is clean. | SQLite (MVP) → PostgreSQL (scale) |
| **GraphQL** | Adds complexity for no benefit. This is a consumption-heavy app (read > write), not a collaboration platform. REST is simpler and sufficient. | REST API |
| **React** | Pre-selected Vue. Mixing ecosystems creates dependency hell. | Vue 3 |
| **jQuery-based UI libs** | Antiquated, bundle bloat, doesn't integrate with Vue reactivity. Avoid any lib that ships jQuery. | Naive UI |

## Stack Patterns by Variant

**If scaling beyond SQLite (10K+ concurrent users):**
- Swap `sqlite+aiosqlite` → `postgresql+asyncpg` in SQLAlchemy connection string
- Add `asyncpg` dependency
- No code changes needed (SQLAlchemy abstracts the dialect)
- Add Redis for caching frequently-accessed POI data

**If adding user accounts / auth:**
- Add `python-jose[cryptography]` for JWT tokens
- Add `passlib[bcrypt]` for password hashing
- Use FastAPI's `Depends()` for auth middleware
- Add `users` and `sessions` tables via Alembic migration

**If adding real-time collaboration:**
- FastAPI supports WebSocket natively
- Add `websockets` library (uvicorn already supports it)
- Use for live itinerary editing between multiple users

**If needing background job processing:**
- Start with `asyncio.create_task()` for simple async jobs
- Graduate to `arq` (lightweight, Redis-backed) if persistence needed
- Don't jump to Celery unless you have heavy CPU-bound workloads

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.135.3 | Pydantic 2.x (2.13.1) | FastAPI requires Pydantic v2 since 0.100+. |
| SQLAlchemy 2.0.49 | aiosqlite 0.22.1 | Use `sqlite+aiosqlite://` dialect string. |
| SQLAlchemy 2.0.49 | alembic 1.18.4 | Standard pairing. Alembic auto-generates from SQLAlchemy models. |
| Vue 3.5.32 | Pinia 3.0.4 | Pinia 3.0 requires Vue 3.x. ✓ |
| Vue 3.5.32 | Naive UI 2.44.1 | Naive UI requires Vue ^3.0.0. ✓ |
| Vue 3.5.32 | vue-router 5.0.4 | vue-router 5.x requires Vue 3.3+. ✓ |
| Vite 8.0.8 | @vitejs/plugin-vue 6.0.6 | Plugin compatible with Vite 5-8. ✓ |
| Tailwind 4.2.2 | Vite 8.0.8 | Use `@tailwindcss/vite` plugin, NOT PostCSS plugin. Tailwind v4 changed the integration model. |
| openai 2.31.0 | httpx 0.28.1 | openai SDK uses httpx internally. No conflict. |
| Python 3.12 | aiosqlite 0.22.1 | Requires Python ≥3.9. ✓ |

## Sources

- **FastAPI** — GitHub releases (verified 0.135.3, 2026-04-01). Built-in SSE in 0.135.0 confirmed.
- **Vue 3** — GitHub releases (verified 3.5.32, 2026-04-03).
- **SQLAlchemy** — GitHub releases (verified 2.0.49, 2026-04-03).
- **Pydantic** — GitHub releases (verified 2.13.1, 2026-04-15).
- **Vite** — GitHub releases (verified 8.0.8, 2026-04-09).
- **Pinia** — GitHub releases (verified 3.0.4, 2025-11-05).
- **uvicorn** — GitHub releases (verified 0.44.0, 2026-04-06).
- **openai-python** — GitHub releases (verified 2.31.0, 2026-04-08).
- **Naive UI** — npm registry (verified 2.44.1).
- **Tailwind CSS** — npm registry (verified 4.2.2).
- **DeepSeek API** — Official docs: openai-compatible format, `deepseek-chat` = V3.2, 128K context, `base_url='https://api.deepseek.com'`.
- **httpx** — GitHub releases (verified 0.28.1, 2024-12-06). Stable but release cadence slowed.
- **aiosqlite** — PyPI JSON API (verified 0.22.1, 2025-12-23).
- **alembic** — PyPI JSON API (verified 1.18.4).
- **ruff** — PyPI JSON API (verified 0.15.10).
- **@vitejs/plugin-vue** — npm registry (verified 6.0.6).

---
*Stack research for: 拾途 (Shí Tú) — Taste-based Itinerary Generator*
*Researched: 2026-04-15*
