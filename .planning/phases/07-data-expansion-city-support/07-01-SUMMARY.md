---
phase: 07-data-expansion-city-support
plan: 01
subsystem: city-config
tags: [config, data, multi-city]
dependency_graph:
  requires: []
  provides: [city-config-loader, multi-city-support]
  affects: [stage1_intent, generate-route]
tech_stack:
  added: [pydantic-city-config, lru_cache-loader]
  patterns: [file-driven-config, pydantic-validation]
key_files:
  created:
    - data/cities/shanghai.json
    - data/cities/hangzhou.json
    - src/backend/services/city_config.py
  modified:
    - src/backend/pipeline/stages/stage1_intent.py
    - src/backend/api/routes/generate.py
decisions:
  - Pydantic CityConfig model for schema validation on load
  - lru_cache on _load_all_cities for single-load-per-process
  - File-based config — adding a city = dropping a JSON file, no code changes
  - Supported interests for Shanghai expanded to include all 27 taste_tags from actual POI data
metrics:
  duration: 224s
  completed: "2026-04-17"
  tasks: 2
  files: 5
---

# Phase 7 Plan 1: City Config System Summary

Config-driven city support replacing hardcoded references — adding a new city now means dropping a JSON file with zero code changes.

## What Was Done

### Task 1: Create city config files and loader module
- Created `data/cities/shanghai.json` with center coords (31.2304, 121.4737), bounds, 27 supported interests (expanded to match all actual POI taste_tags)
- Created `data/cities/hangzhou.json` with center coords (30.2741, 120.1551), bounds, 13 supported interests
- Created `src/backend/services/city_config.py` with Pydantic-validated loader, `lru_cache` for single-load, exports: `get_city_config`, `get_supported_cities`, `is_city_supported`, `get_supported_cities_display`

### Task 2: Integrate city config into pipeline and API
- Replaced hardcoded `("上海",)` check in `stage1_intent.py` with `is_city_supported()` call
- Removed `SUPPORTED_CITIES = {"上海"}` from `generate.py`, replaced with import of `get_supported_cities`
- Error messages now dynamically list all configured cities

## Verification Results

- `get_supported_cities()` returns `{'上海', '杭州'}`
- `is_city_supported('杭州')` returns True
- `is_city_supported('北京')` returns False
- No hardcoded city names in stage1_intent.py validation logic
- No `SUPPORTED_CITIES` constant in generate.py
- City config centers validated (e.g., Hangzhou lat=30.2741)

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Commit | Description |
|--------|-------------|
| 1e3403f | feat(07-01): create city config files and loader module |
| 7aa7027 | feat(07-01): integrate city config into pipeline and API |

## Self-Check: PASSED

All 6 files exist. Both commits (1e3403f, 7aa7027) confirmed in git log.
