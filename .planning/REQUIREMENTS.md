# Requirements: 拾途 (Shí Tú)

**Defined:** 2026-04-16
**Core Value:** 帮你发现你会喜欢但自己找不到的地方，并且用对的方式推荐给你——品味数据 + SOUL 提示词的组合，让行程有"本地朋友推荐"的温度

## v1.1 Requirements

Requirements for Pipeline Quality + UI Redesign milestone. Each maps to roadmap phases.

### Pipeline & Data

- [x] **PIPE-01**: Stage 2 calls Amap `search_pois()` dynamically based on user intent (city + interests), merges results with curated DB POIs, deduplicates by amap_id
- [ ] **PIPE-02**: AmapCache fully enabled — `get_amap_service()` accepts DB session dependency, all search_pois and get_walking_route results cached with TTL (30d routes, 7d POI)
- [x] **PIPE-03**: User taste preferences (`taste_tags_default`, `budget_default`) injected into pipeline — read from User model in generate route, passed to intent extraction and POI filter stages
- [ ] **PIPE-04**: Test Runner fixed — import paths use `from backend.config`, async engine uses correct `+aiosqlite` URL, `/test-runner/generate` produces A/B/C itineraries for all scenarios

### Cities & Data

- [x] **CITY-01**: Second city (Hangzhou) POI data curated — Tier A (12 entries), Tier B (6 entries), Tier C chains/budget (3 entries) with is_chain field
- [x] **CITY-02**: City config model (`data/cities/{city}.json`) with name, center coordinates, bounds, default zoom, supported interests — pipeline reads config instead of hardcoding "上海"
- [x] **CITY-03**: DB auto-seeds POIs + scenarios on startup if tables empty — glob auto-discovery, no manual script required for fresh deploy
- [x] **CITY-04**: Tier C data included — chain restaurants, budget cafés (is_chain field, rating >3.0) to provide economy options

### Auth & User

- [ ] **AUTH-01**: Auth backend verified working — bcrypt replacement tested end-to-end, register creates user, login returns JWT, `/me` returns profile
- [ ] **AUTH-02**: Frontend login/register modal with email + password form, JWT stored in localStorage, auto-attached to all API requests via interceptor
- [ ] **AUTH-03**: Route guard redirects unauthenticated users to login for protected pages (itinerary list, settings)
- [ ] **AUTH-04**: User settings page — display and edit `taste_tags_default` (tag selector) and `budget_default` (radio buttons for 3 options), PUT `/auth/profile` endpoint
- [ ] **AUTH-05**: Itinerary list page — GET `/itineraries` by user_id, displays cards with title/city/date, click navigates to itinerary view

### UI Redesign

- [ ] **UI-01**: Full frontend redesign using ui-ux-pro-max — bright warm palette (sand/coral/ocean), exciting "旅途中" feel, card-based layout with depth and warmth
- [ ] **UI-02**: POI detail card displays `highlight_note` (推荐理由), `vibe_description` (氛围描述), `tier` badge (★/○/·), `walk_to_next_minutes`, and opening hours
- [ ] **UI-03**: Data provenance — each POI shows source attribution: "人工精选" for Tier A, "高德地图" for Amap-sourced, "AI推荐" for LLM-suggested; reference icon/badge
- [ ] **UI-04**: Generation loading experience redesigned — journey-themed animation/progress, stage messages with travel imagery feel, not sterile progress bars
- [ ] **UI-05**: Home page excites — hero area with emotional pull, example prompts as clickable journey cards, not plain tags

### Map & Visualization

- [ ] **MAP-01**: Amap JS map component integrated — displays POI markers with tier-colored pins (gold=A, silver=B, bronze=C), walking route lines between consecutive POIs
- [ ] **MAP-02**: Map-timeline bidirectional sync — click POI in timeline highlights map marker and pans; click map marker expands timeline POI
- [ ] **MAP-03**: Day routes color-coded on map (Day 1 blue, Day 2 green, Day 3 orange); map auto-zooms to fit selected day's POIs
- [ ] **MAP-04**: Map responsive — split view on desktop (map left/right + timeline), tabbed/stacked on mobile

### Sharing

- [ ] **SHARE-01**: Itinerary sharing — "复制链接" button copies `/itinerary/{id}` URL, dynamic `og:title` and `og:description` meta tags set from itinerary title/summary
- [ ] **SHARE-02**: Share button accessible from itinerary view header; success toast on copy

### Infrastructure

- [ ] **INFRA-01**: Alembic initialized with initial migration reflecting current models — future schema changes via `alembic revision --autogenerate`
- [ ] **INFRA-02**: JWT production guard — backend refuses to start if `JWT_SECRET_KEY` not set and `ENVIRONMENT=production`
- [ ] **INFRA-03**: seed_pois.py fixed — `lat`/`lng` kwargs changed to `latitude`/`longitude`; imports use `backend.` prefix

## v1.2 Requirements

Deferred to next milestone. Tracked but not in current roadmap.

### Testing & Quality

- **TEST-01**: Pytest suite with unit tests for pipeline stages, integration tests for API endpoints
- **TEST-02**: Rate limiting middleware on `/api/generate` (10 req/min per IP)
- **TEST-03**: Structured JSON logging with request correlation IDs

### Performance & Ops

- **PERF-01**: SQLite WAL mode enabled via engine pragmas
- **PERF-02**: Composite index `(city, tier)` on `pois` table
- **PERF-03**: HTTPS with Let's Encrypt in nginx
- **PERF-04**: Security headers (CSP, HSTS, X-Frame-Options)
- **PERF-05**: Docker healthcheck in docker-compose.yml

### UX Enhancements

- **UX-01**: Dark mode toggle
- **UX-02**: PWA support (service worker, manifest.json)
- **UX-03**: POI photos from 高德/Unsplash
- **UX-04**: Reconnection UI for interrupted generations

## Out of Scope

| Feature | Reason |
|---------|--------|
| 支付/预订功能 | 非旅行规划核心 |
| 多语言 | 目标用户为中国用户 |
| App 端 | Web only，后续可迁移微信小程序 |
| 多城市/跨城行程 | v1.1 只加第二个城市，跨城不在此范围 |
| 实时价格比价 | 数据获取困难，非核心 |
| D2/D4/D5/D6/D8 维度评分 | post-MVP 扩展 |
| Fine-tuning 模型 | 品味来自数据 + SOUL 提示词 |
| Offline mode | 需要网络连接 |
| Real-time collaboration | 过度复杂，非核心 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 6 | Pending |
| INFRA-02 | Phase 6 | Pending |
| INFRA-03 | Phase 6 | Pending |
| PIPE-02 | Phase 6 | Pending |
| PIPE-04 | Phase 6 | Pending |
| CITY-01 | Phase 7 | Complete |
| CITY-02 | Phase 7 | Complete |
| CITY-03 | Phase 7 | Complete |
| CITY-04 | Phase 7 | Complete |
| PIPE-01 | Phase 7 | Complete |
| PIPE-03 | Phase 7 | Complete |
| AUTH-01 | Phase 8 | Pending |
| AUTH-02 | Phase 8 | Pending |
| AUTH-03 | Phase 8 | Pending |
| AUTH-04 | Phase 8 | Pending |
| AUTH-05 | Phase 8 | Pending |
| UI-01 | Phase 9 | Pending |
| UI-02 | Phase 9 | Pending |
| UI-03 | Phase 9 | Pending |
| UI-04 | Phase 9 | Pending |
| UI-05 | Phase 9 | Pending |
| MAP-01 | Phase 10 | Pending |
| MAP-02 | Phase 10 | Pending |
| MAP-03 | Phase 10 | Pending |
| MAP-04 | Phase 10 | Pending |
| SHARE-01 | Phase 10 | Pending |
| SHARE-02 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-17 — Phase 7 complete, CITY-01/03/04 marked done, PIPE-03 user_prefs wired to stage1*
