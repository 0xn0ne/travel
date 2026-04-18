---
phase: 07-data-expansion-city-support
plan: 03
subsystem: pipeline-dynamic-expansion
tags: [amap, dynamic-poi, user-preferences, scoring]
dependency_graph:
  requires: [07-01-city-config, 07-02-poi-data]
  provides: [dynamic-amap-expansion, user-prefs-passthrough]
  affects: [stage2_filter, coordinator, generate-route]
tech_stack:
  added: [amap-batch-search, determine_tier-auto-tiering]
  patterns: [optional-service-injection, user-prefs-scoring-boost]
key_files:
  created:
    - tests/test_stage2_expansion.py
  modified:
    - src/backend/pipeline/stages/stage2_filter.py
    - src/backend/pipeline/stages/stage1_intent.py
    - src/backend/pipeline/coordinator.py
    - src/backend/api/routes/generate.py
decisions:
  - Amap expansion limited to top 5 interests × 10 results per keyword (max 50 API calls)
  - Amap failures degrade gracefully to DB-only with warning log
  - User taste_tags merged into scoring_interests (not replacing intent.interests)
  - Auto-tiering uses existing determine_tier() from seed_pois for consistency
  - Curated DB POIs always win dedup conflicts (trust curated data over Amap)
metrics:
  duration: 426s
  completed: "2026-04-17"
  tasks: 2
  files: 4
---

# Phase 7 Plan 3: Dynamic Amap Expansion + User Prefs Summary

Stage 2 filter now dynamically expands POI pool via Amap search and user preferences flow from API through coordinator to scoring.

## What Was Done

### Task 1: Add Amap dynamic expansion to Stage 2 filter (TDD)
- **RED**: Created `tests/test_stage2_expansion.py` with 6 tests covering backward compat, Amap merge, dedup, auto-tiering, cap/floor, and user prefs boost
- **GREEN**: Modified `stage2_filter.py` to accept `amap_service` and `user_prefs` params, added Amap expansion block, `_amap_to_candidate` converter, dedup by `amap_id`, and user taste_tags merged into `scoring_interests`
- All 6 tests pass, backward compatible when `amap_service=None`

### Task 2: Wire user preferences through API → Coordinator → stage1 + filter_pois
- `generate.py`: Extract `taste_tags_default` (JSON parse) and `budget_default` from authenticated user, pass as `user_prefs` dict to coordinator
- `coordinator.py`: Added `_user_prefs` attribute, passes to both `extract_intent` (stage1) and `filter_pois` (stage2) in `_run_pipeline_async` and `adjust_pipeline`
- `stage1_intent.py`: Accepts optional `user_prefs`, injects user taste tags and budget as system message hints for more accurate intent extraction

## Verification Results

- 6/6 tests pass in `tests/test_stage2_expansion.py`
- `filter_pois` signature includes `amap_service` and `user_prefs` params
- `extract_intent` signature includes `user_prefs` param
- Coordinator `__init__` has `_user_prefs`
- Both `_run_pipeline_async` and `adjust_pipeline` pass `amap_service=` and `user_prefs=` to `filter_pois`
- `_run_pipeline_async` passes `user_prefs=self._user_prefs` to `extract_intent`
- `generate.py` extracts and passes `_user_prefs` from `current_user`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixture not async — seeded_db coroutine never awaited**
- **Found during:** Task 1 RED phase
- **Issue:** `seeded_db` fixture returned a coroutine instead of awaiting it
- **Fix:** Changed from `def` fixture returning coroutine to `async def` fixture directly awaiting
- **Files modified:** `tests/test_stage2_expansion.py`

**2. [Rule 1 - Bug] Insufficient Tier A POIs caused B/C cap too small for Amap results**
- **Found during:** Task 1 GREEN phase
- **Issue:** With only 1 Tier A POI, the 40% floor limited B/C pool to 1 slot, so Amap POIs couldn't appear in results
- **Fix:** Added 3 more Tier A POIs to seed data (total 4 Tier A, 2 Tier B/C) so the floor allows adequate B/C slots
- **Files modified:** `tests/test_stage2_expansion.py`

## Commits

| Commit | Description |
|--------|-------------|
| 947f335 | test(07-03): add failing tests for Stage 2 Amap expansion and user prefs |
| 403b475 | feat(07-03): add Amap dynamic POI expansion and user prefs to Stage 2 |
| 681b969 | feat(07-03): wire user preferences through API → coordinator → filter_pois |

## Self-Check: PASSED

All 4 files exist. All 3 commits (947f335, 403b475, 681b969) confirmed in git log.
