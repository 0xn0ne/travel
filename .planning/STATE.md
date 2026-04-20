---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: AI Agent Tool System
status: planning
stopped_at: Not started
last_updated: "2026-04-20T00:00:00.000Z"
last_activity: 2026-04-20 -- Milestone v1.2 started
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-20)

**Core value:** 帮你发现你会喜欢但自己找不到的地方，并且用对的方式推荐给你——品味数据 + SOUL 提示词的组合，让行程有"本地朋友推荐"的温度
**Current focus:** v1.2 AI Agent Tool System — defining requirements

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-20 — Milestone v1.2 started

## Accumulated Context

### Decisions (from v1.1)

- Alembic owns schema via programmatic upgrade; Base.metadata.create_all removed
- JWT guard uses runtime check in lifespan; blocks startup in production without secret
- Auto-seed checks row count, only inserts on empty tables (idempotent)
- AmapService is request-scoped (not singleton); cache uses request DB session
- AsyncSessionFactory accessed via module import (not direct name import) due to late-init global
- File-based city config — adding a city = drop JSON in data/cities/, no code changes
- Amap expansion limited to 5 keywords × 10 results; failures degrade to DB-only
- User taste_tags merged into scoring_interests alongside intent.interests
- Auto-tiering uses determine_tier() for consistency between seed and expansion
- Placeholder amap_ids (curated_hz_XXX) for curated Hangzhou data; real IDs backfill later

### v1.1 Accomplishments

- **Phase 6:** Alembic migrations, JWT production guard, AmapService cache injection, test runner fix
- **Phase 7:** City config system, Hangzhou POI data (21 POIs), multi-city auto-seeding, dynamic Amap POI expansion, user preferences pipeline
- **Phase 8:** Auth backend + frontend (11 tests), AuthModal, SettingsView, ItineraryListView
- **Phase 9:** Warm design system (25+ CSS vars), rich POI cards, hero gradient, journey-themed progress
- **Phase 10:** Map integration (Amap JS), bidirectional sync, day route colors, sharing

### Pending Todos

None from v1.1.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-04-20
Status: **Defining v1.2 requirements**
Next: Complete requirements → roadmap → execute
